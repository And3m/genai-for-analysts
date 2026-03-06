# 01 — Automated Report Narrator

## Problem Statement

Business analysts spend hours every week writing the same style of narrative commentary on top of data exports — "Revenue grew 12% QoQ driven by the APAC region..." This project automates that. Feed it a CSV or Excel file, and it produces a polished written business summary ready for an executive email or slide deck.

## Architecture

```mermaid
flowchart LR
    A[CSV / Excel Upload] --> B[pandas: compute stats]
    B --> C[Jinja2: build prompt]
    C --> D[Anthropic Claude API]
    D --> E[Business Narrative Output]
    E --> F[Streamlit UI / Email Export]
```

## Setup

```bash
cd 01-report-narrator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
streamlit run app.py
```

## Usage

1. Upload a CSV or Excel file via the Streamlit sidebar
2. Select the columns representing dates, metrics, and dimensions
3. Click "Generate Narrative"
4. Copy the output or download as a `.txt` file

## Business Value

- **Time saved:** ~2–3 hours/week per analyst writing routine commentary
- **Consistency:** Same tone and structure every report cycle
- **Scalability:** Works on any tabular dataset without code changes

## What I Learned

- Prompt engineering for structured business writing (tone, length, format control)
- Jinja2 templating to dynamically inject stats into prompts
- Anthropic SDK streaming for real-time output display

## Limitations & Future Work

- Currently supports single-table CSVs; multi-table joins planned
- No chart generation yet — Matplotlib integration is next
- Add memory of previous periods for YoY/MoM language
