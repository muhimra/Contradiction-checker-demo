import pdfplumber
import json
import os
import re
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[63:70]:  # Adjust page range as needed
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def get_structured_claims(report_text):
    prompt = f"""
    Analyze the following text from a McKinsey research report. 
    Extract 10-15 specific, measurable, and falsifiable claims.
    
    A claim is valid if:
    1. It mentions a specific metric (e.g., GDP, ROI, percentage shift).
    2. It has a geographic or industry scope.
    3. It refers to a specific timeframe.

    Exclude illustrative examples, hypotheticals, and recommendations. 
    Only extract claims that cite a specific statistic or data point.

    Return ONLY a JSON list of objects with this structure, no markdown fences:
    [
        {{
            "claim": "The exact or paraphrased claim",
            "type": "Economic/Industry/Social",
            "domain": "e.g., Energy Transition",
            "implied_timeframe": "e.g., 2021-2023",
            "measurable": true
        }}
    ]

    Text:
    {report_text}
    """

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        temperature=0,
        system="You are a clinical data auditor. Extract only hard facts, no fluff. Return only raw JSON, no markdown.",
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

if __name__ == "__main__":
    raw_text = extract_text_from_pdf("data/reportocr.pdf")

    if not raw_text.strip():
        print("ERROR: No text extracted from PDF. Check the file path and that the PDF isn't scanned/image-only.")
        exit(1)

    print(f"Extracted {len(raw_text)} characters from PDF...")
    claims_string = get_structured_claims(raw_text)

    os.makedirs("output", exist_ok=True)

    try:
        # Strip markdown fences if model added them anyway
        cleaned = re.sub(r"```json\s*|\s*```", "", claims_string).strip()
        data = json.loads(cleaned)
        with open("output/claims.json", "w") as f:
            json.dump(data, f, indent=4)
        print(f"Success! Extracted {len(data)} claims. Check output/claims.json")
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print("Raw output from Claude:")
        print(claims_string)
        # Save raw output anyway so you don't lose it
        with open("output/claims_raw.txt", "w") as f:
            f.write(claims_string)
        print("Raw output saved to output/claims_raw.txt")