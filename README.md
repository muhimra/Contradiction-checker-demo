# McKinsey Claim Auditor

An automated fact-checking pipeline that extracts measurable claims from industry reports, routes each claim to the right public data source, and returns structured verdicts.

Built to answer a simple question: *when a consulting firm publishes a statistic, how hard is it to verify?*

![Dashboard screenshot](dashboard_screenshot.png)

---

## How it works

The pipeline runs in three stages:

**1. Claim extraction**
Ingests a PDF or text document and uses Claude API to extract specific, measurable, falsifiable claims — filtering out anecdotes, hypotheticals, and recommendations.

**2. Evidence routing**
For each claim, a routing call generates a targeted search query and identifies the most appropriate source type (SEC filing, government database, press release, academic paper). Web search retrieves live evidence.

**3. Verdict classification**
Claude compares the claim against the retrieved evidence and returns a structured verdict:
- ✅ Supported
- ⚠️ Partially Supported
- ❌ Contradicted
- ❓ Unverifiable

Each verdict includes a confidence level, reasoning, source quality rating, and a flag for claims that are technically accurate but misleading in context.

---

## Key finding

Tested against McKinsey Quarterly Q2 2026 — specifically the Jane Fraser / Citigroup interview.

McKinsey reported Citi's 30,000 developers are **"9% more productive"**. Citi's own SEC filing reports the same cohort generated **100,000 additional hours of weekly capacity**.

These look inconsistent — until you do the maths:

```
100,000 hrs ÷ 30,000 devs = 3.3 extra hrs/dev/week
3.3 ÷ 40 hr week = ~8.3% productivity gain
```

Same figure. Different audience. Different frame. The pipeline surfaced the discrepancy — the analysis resolved it.

---

## Stack

| Layer | Tool |
|---|---|
| Claim extraction | Claude API (Haiku) |
| Verdict classification | Claude API (Sonnet) |
| Evidence retrieval | Anthropic web search tool |
| PDF parsing | pdfplumber |
| Dashboard | Streamlit |
| Vector similarity | sentence-transformers + ChromaDB |

---

## Setup

```bash
git clone https://github.com/yourusername/mckinsey-claim-auditor
cd mckinsey-claim-auditor
pip install -r requirements.txt
```

Add your Anthropic API key to a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
```

Place your report as `data/report.txt` (copy-paste text from the source document).

---

## Usage

```bash
# Step 1 — extract claims
python extract_claims.py

# Step 2 — verify claims against live data
python verify_claims.py

# Step 3 — view results
streamlit run dashboard.py
```

Results are saved to `output/verdicts.json`.

---

## Project structure

```
mckinsey-claim-auditor/
├── data/
│   └── report.txt          # Input document
├── output/
│   ├── claims.json         # Extracted claims
│   └── verdicts.json       # Verified verdicts
├── extract_claims.py       # Stage 1: claim extraction
├── verify_claims.py        # Stage 2: evidence + verdict
├── dashboard.py            # Streamlit UI
├── .env                    # API key (not committed)
└── README.md
```

---

## Limitations

- Verdict quality depends on what public evidence exists — some claims are genuinely unverifiable from open sources
- A single report is a small sample; contradictions are more meaningful across a larger corpus
- The pipeline flags discrepancies for human review — it is not a replacement for manual verification

---

## Built by

[Exorank](https://yourwebsite.com) — AI workflow consulting
