# GenAI Portfolio — Business Analyst Edition

A 10-project portfolio demonstrating GenAI engineering skills built on a foundation of 13+ years in data analytics, BI, and reporting automation. Each project is framed as a real enterprise problem, not a tutorial exercise.

---

## Projects

| # | Project | Phase | Status |
|---|---|---|---|
| 01 | [Automated Report Narrator](./01-report-narrator/) | LLM Foundations | Scaffolded |
| 02 | [Prompt Engineering Playground](./02-prompt-playground/) | LLM Foundations | Scaffolded |
| 03 | [Policy / SOP Q&A Bot](./03-policy-qa-rag/) | RAG | Scaffolded |
| 04 | [Financial Report Analyst](./04-financial-report-rag/) | RAG | Scaffolded |
| 05 | [Data Analyst Agent](./05-data-analyst-agent/) | Agents & Tool Use | Scaffolded |
| 06 | [Multi-Source Research Agent](./06-research-agent/) | Agents & Tool Use | Scaffolded |
| 07 | [Domain-Specific Text Classifier](./07-fine-tuned-classifier/) | Fine-Tuning | Scaffolded |
| 08 | [RAG Evaluation Dashboard](./08-rag-eval-dashboard/) | Evaluation | Scaffolded |
| 09 | [Guardrailed Enterprise Chatbot](./09-guardrailed-chatbot/) | Guardrails | Scaffolded |
| 10 | [Invoice / Document Intelligence](./10-document-intelligence/) | Multimodal | Scaffolded |

---

## Phases

### Phase 1 — LLM Foundations (Weeks 1–3)
Learn tokenization, prompt engineering, structured output, and cost estimation. Build two tools that directly connect LLMs to business data and reporting workflows.

### Phase 2 — RAG (Weeks 4–7)
Ground LLM responses in your own documents. Build production-style retrieval pipelines over HR policies and financial filings.

### Phase 3 — Agents & Tool Use (Weeks 8–11)
Move beyond single-turn Q&A. Build agents that write and execute code, search the web, and synthesize multi-source research.

### Phase 4 — Fine-Tuning (Weeks 12–14)
Learn when fine-tuning beats prompt engineering. Fine-tune a small model for business document classification with LoRA/QLoRA.

### Phase 5 — Evaluation & Guardrails (Weeks 15–17)
Add rigor. Measure RAG quality with RAGAS/DeepEval and build an enterprise chatbot with safety layers and audit logging.

### Phase 6 — Multimodal & Advanced (Weeks 18–20)
End-to-end document intelligence: upload invoices, extract structured fields with vision LLMs, validate and store.

---

## Tech Stack

| Category | Tools |
|---|---|
| LLM APIs | Anthropic Claude, OpenAI |
| Orchestration | LangChain, LangGraph, LlamaIndex |
| Vector DBs | ChromaDB, FAISS |
| Evaluation | RAGAS, DeepEval |
| Fine-Tuning | Hugging Face, PEFT/LoRA |
| Frontend | Streamlit |
| Observability | Langfuse, Weights & Biases |
| Data | pandas, SQLite |

---

## Setup

Each project is self-contained. See the individual project `README.md` for setup instructions.

Global prerequisites:
- Python 3.11+
- API keys: Anthropic, OpenAI (some projects), Tavily (Project 6)
