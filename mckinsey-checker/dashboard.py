import streamlit as st
import json
import os

st.set_page_config(
    page_title="McKinsey Claim Auditor",
    page_icon="🔍",
    layout="wide"
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0a0a0a;
    color: #e8e8e8;
}

.stApp { background-color: #0a0a0a; }

.header-block {
    border-left: 4px solid #e8c84a;
    padding: 0.4rem 0 0.4rem 1.2rem;
    margin-bottom: 2rem;
}
.header-block h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: #f5f5f5;
    margin: 0;
    letter-spacing: -0.03em;
}
.header-block p {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #888;
    margin: 0.2rem 0 0 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.stat-box {
    background: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 1.2rem 1.4rem;
    text-align: center;
}
.stat-box .num {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1;
}
.stat-box .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.3rem;
}

.claim-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    position: relative;
    transition: border-color 0.2s;
}
.claim-card:hover { border-color: #444; }

.claim-card.contradicted  { border-left: 3px solid #e05555; }
.claim-card.supported     { border-left: 3px solid #4caf7d; }
.claim-card.unverifiable  { border-left: 3px solid #888; }
.claim-card.partially     { border-left: 3px solid #e8a83a; }

.verdict-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    padding: 0.2rem 0.6rem;
    border-radius: 3px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-right: 0.5rem;
}
.pill-contradicted  { background: #2a1212; color: #e05555; border: 1px solid #e05555; }
.pill-supported     { background: #0f2018; color: #4caf7d; border: 1px solid #4caf7d; }
.pill-unverifiable  { background: #1a1a1a; color: #888;    border: 1px solid #555; }
.pill-partially     { background: #261c08; color: #e8a83a; border: 1px solid #e8a83a; }
.pill-flag          { background: #261800; color: #e8c84a; border: 1px solid #e8c84a; }

.confidence-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.claim-text {
    font-size: 1rem;
    font-weight: 600;
    color: #ddd;
    margin: 0.7rem 0 0.5rem 0;
    line-height: 1.4;
}
.reasoning-text {
    font-size: 0.85rem;
    color: #888;
    line-height: 1.6;
    margin-top: 0.5rem;
}
.meta-row {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #555;
    margin-top: 0.8rem;
    padding-top: 0.8rem;
    border-top: 1px solid #1e1e1e;
}
.divider {
    border: none;
    border-top: 1px solid #1e1e1e;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_verdicts(path):
    with open(path) as f:
        return json.load(f)

verdicts_path = "output/verdicts.json"

if not os.path.exists(verdicts_path):
    st.error("No verdicts.json found. Run verify_claims.py first.")
    st.stop()

data = load_verdicts(verdicts_path)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
    <h1>McKinsey Claim Auditor</h1>
    <p>Automated fact-check · Q2 2026 Quarterly</p>
</div>
""", unsafe_allow_html=True)


# ── Summary Stats ─────────────────────────────────────────────────────────────
verdicts = [r.get("verdict", "Error") for r in data]
total        = len(data)
supported    = verdicts.count("Supported")
contradicted = verdicts.count("Contradicted")
unverifiable = verdicts.count("Unverifiable")
partial      = verdicts.count("Partially Supported")
flagged      = sum(1 for r in data if r.get("flag"))

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f'<div class="stat-box"><div class="num" style="color:#f5f5f5">{total}</div><div class="label">Claims Checked</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-box"><div class="num" style="color:#4caf7d">{supported}</div><div class="label">Supported</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-box"><div class="num" style="color:#e05555">{contradicted}</div><div class="label">Contradicted</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-box"><div class="num" style="color:#888">{unverifiable}</div><div class="label">Unverifiable</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="stat-box"><div class="num" style="color:#e8c84a">{flagged}</div><div class="label">Flagged</div></div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 1])

with col_f1:
    filter_verdict = st.multiselect(
        "Filter by verdict",
        options=["Supported", "Contradicted", "Unverifiable", "Partially Supported"],
        default=["Supported", "Contradicted", "Unverifiable", "Partially Supported"]
    )
with col_f2:
    show_flagged_only = st.toggle("Show flagged only", value=False)

filtered = [
    r for r in data
    if r.get("verdict") in filter_verdict
    and (not show_flagged_only or r.get("flag"))
]

st.markdown(f'<p style="font-family: JetBrains Mono, monospace; font-size: 0.72rem; color: #555; margin-bottom: 1.2rem;">SHOWING {len(filtered)} OF {total} CLAIMS</p>', unsafe_allow_html=True)


# ── Claim Cards ───────────────────────────────────────────────────────────────
VERDICT_CLASS = {
    "Contradicted":       "contradicted",
    "Supported":          "supported",
    "Unverifiable":       "unverifiable",
    "Partially Supported": "partially",
}
PILL_CLASS = {
    "Contradicted":       "pill-contradicted",
    "Supported":          "pill-supported",
    "Unverifiable":       "pill-unverifiable",
    "Partially Supported": "pill-partially",
}

for r in filtered:
    verdict  = r.get("verdict", "Unknown")
    flagged  = r.get("flag", False)
    card_cls = VERDICT_CLASS.get(verdict, "unverifiable")
    pill_cls = PILL_CLASS.get(verdict, "pill-unverifiable")
    conf     = r.get("confidence", "")
    flag_html = '<span class="verdict-pill pill-flag">⚑ Flagged</span>' if flagged else ""

    st.markdown(f"""
    <div class="claim-card {card_cls}">
        <span class="verdict-pill {pill_cls}">{verdict}</span>
        {flag_html}
        <span class="confidence-tag">· {conf} confidence</span>
        <div class="claim-text">"{r.get('claim', '')}"</div>
        <div class="reasoning-text">{r.get('reasoning', '')}</div>
        <div class="meta-row">
            Domain: {r.get('domain', '—')} &nbsp;·&nbsp;
            Timeframe: {r.get('timeframe', '—')} &nbsp;·&nbsp;
            Source quality: {r.get('source_quality', '—')} &nbsp;·&nbsp;
            Query: {r.get('search_query', '—')}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<p style="font-family: JetBrains Mono, monospace; font-size: 0.68rem; color: #444; text-align: center;">
    Built with Claude API · Haiku for extraction · Sonnet for verdicts · Web search for evidence
</p>
""", unsafe_allow_html=True)
