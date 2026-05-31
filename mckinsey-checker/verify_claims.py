import json
import os
import re
import time
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────────
# STEP 1: ROUTER
# Decides what to search for and where to look
# ─────────────────────────────────────────────
def get_search_strategy(claim: dict) -> dict:
    """
    Ask Claude: given this claim, what search query would find evidence for it?
    Returns a search query and the type of source to prioritise.
    
    We use Haiku here because this is a simple routing decision — no need
    for expensive model judgement yet.
    """
    prompt = f"""
    Given this claim from a McKinsey report, suggest the best web search query
    to find evidence that would verify or contradict it.
    
    Claim: {claim['claim']}
    Domain: {claim['domain']}
    Timeframe: {claim['implied_timeframe']}
    
    Return ONLY raw JSON, no markdown:
    {{
        "search_query": "the exact query to run",
        "source_priority": "e.g. company annual report / government data / press release / academic paper",
        "what_to_look_for": "specifically what number or fact would confirm or deny this"
    }}
    """
    
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        temperature=0,
        system="You are a research assistant. Return only raw JSON.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = message.content[0].text
    cleaned = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────
# STEP 2: WEB SEARCH
# Uses Claude's built-in web search tool to fetch evidence
# ─────────────────────────────────────────────
def fetch_evidence(search_query: str) -> str:
    """
    Run a web search using Claude's web_search tool.
    Returns the raw text evidence found.
    
    This uses the web_search tool built into the Anthropic API —
    Claude searches the web and returns what it finds as part of its response.
    We extract only the text blocks (ignoring the tool_use metadata blocks).
    """
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        system="You are a research assistant. Search for the given query and summarise the key facts found. Be specific about numbers and dates.",
        messages=[{
            "role": "user",
            "content": f"Search for: {search_query}. Return a factual summary of what you find, focusing on specific numbers, dates, and sources."
        }]
    )
    
    # The response contains multiple content blocks:
    # - type "text": Claude's actual summary (what we want)
    # - type "tool_use": metadata about the search call (ignore this)
    # - type "tool_result": raw search results (ignore this)
    # We join all text blocks into one evidence string.
    text_blocks = [block.text for block in message.content if block.type == "text"]
    return " ".join(text_blocks) if text_blocks else "No evidence found."


# ─────────────────────────────────────────────
# STEP 3: VERDICT
# Compares the claim against the evidence
# ─────────────────────────────────────────────
def get_verdict(claim: dict, evidence: str, what_to_look_for: str) -> dict:
    """
    Ask Claude to compare the claim against the evidence and return a verdict.
    
    We use Sonnet here (not Haiku) because this is a nuanced judgement call —
    the model needs to distinguish between "supported", "partially supported",
    "contradicted", and "unverifiable". Haiku would be less reliable here.
    """
    prompt = f"""
    You are fact-checking a claim made in a McKinsey Quarterly report.
    
    CLAIM: {claim['claim']}
    
    WHAT TO LOOK FOR: {what_to_look_for}
    
    EVIDENCE FOUND:
    {evidence}
    
    Based on the evidence, return ONLY raw JSON with your verdict:
    {{
        "verdict": "Supported / Partially Supported / Contradicted / Unverifiable",
        "confidence": "High / Medium / Low",
        "reasoning": "1-2 sentences explaining why",
        "source_quality": "Strong / Adequate / Weak",
        "flag": true or false  
    }}
    
    Set flag to true if the claim appears misleading, exaggerated, or lacks context
    even if technically supported.
    """
    
    message = client.messages.create(
        model="claude-sonnet-4-6",   # Sonnet for nuanced judgement
        max_tokens=400,
        temperature=0,
        system="You are a rigorous fact-checker. Be skeptical. Return only raw JSON.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = message.content[0].text
    cleaned = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────
# MAIN PIPELINE
# Runs all three steps for every claim in claims.json
# ─────────────────────────────────────────────
def run_pipeline(claims_path: str, output_path: str):
    with open(claims_path, "r") as f:
        claims = json.load(f)
    
    results = []
    
    for i, claim in enumerate(claims):
        print(f"\n[{i+1}/{len(claims)}] Checking: {claim['claim'][:70]}...")
        
        try:
            # Step 1: decide what to search for
            strategy = get_search_strategy(claim)
            print(f"  → Searching: {strategy['search_query']}")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
            # Step 2: fetch evidence from the web
            evidence = fetch_evidence(strategy['search_query'])
            print(f"  → Evidence fetched ({len(evidence)} chars)")
            
            time.sleep(1)
            
            # Step 3: get verdict by comparing claim to evidence
            verdict = get_verdict(claim, evidence, strategy['what_to_look_for'])
            print(f"  → Verdict: {verdict['verdict']} (confidence: {verdict['confidence']})")
            
            # Combine everything into one result object
            results.append({
                "claim": claim['claim'],
                "domain": claim['domain'],
                "timeframe": claim['implied_timeframe'],
                "search_query": strategy['search_query'],
                "source_priority": strategy['source_priority'],
                "evidence_summary": evidence[:300],  # truncate for readability
                **verdict  # unpack verdict fields directly into result
            })
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "claim": claim['claim'],
                "domain": claim['domain'],
                "verdict": "Error",
                "error": str(e)
            })
        
        # Pause between claims to stay within API rate limits
        time.sleep(2)
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    
    # Print summary
    print("\n" + "="*50)
    print("AUDIT COMPLETE")
    print("="*50)
    verdicts = [r.get('verdict', 'Error') for r in results]
    for v in ["Supported", "Partially Supported", "Contradicted", "Unverifiable", "Error"]:
        count = verdicts.count(v)
        if count:
            print(f"  {v}: {count}")
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    run_pipeline(
        claims_path="output/claims.json",
        output_path="output/verdicts.json"
    )
