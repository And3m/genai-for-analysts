"""
Financial Report Analyst — Streamlit Q&A App
Entry point: streamlit run app.py
"""

import os
import anthropic
import streamlit as st
from dotenv import load_dotenv
from retriever import retrieve

load_dotenv()

st.set_page_config(page_title="Financial Report Analyst", page_icon="📈", layout="wide")
st.title("Financial Report Analyst")
st.caption("Ask questions about ingested annual reports and 10-K filings. Answers cite specific pages.")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SAMPLE_QUESTIONS = [
    "What were the key risk factors mentioned?",
    "Summarise the revenue trend over the reporting period.",
    "What is the company's liquidity position?",
    "What major acquisitions or divestitures occurred?",
    "What guidance did management provide for the next period?",
]

with st.sidebar:
    st.subheader("Sample questions")
    for q in SAMPLE_QUESTIONS:
        st.markdown(f"- {q}")
    top_k = st.slider("Chunks to retrieve", 3, 10, 5)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask about the financial reports...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("Retrieving relevant sections..."):
        chunks = retrieve(user_query, top_k=top_k)

    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}" for c in chunks
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are a financial analyst assistant. Answer questions using ONLY the provided excerpts "
            "from financial reports. Always cite the source document and page number. "
            "If the information is not in the provided context, say so clearly."
        ),
        messages=[{
            "role": "user",
            "content": f"Financial report excerpts:\n\n{context}\n\n---\n\nQuestion: {user_query}"
        }],
    )

    answer = response.content[0].text

    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("Source chunks retrieved"):
            for c in chunks:
                st.markdown(f"**{c['source']}** — Page {c['page']} (score: {c['score']:.3f})")
                st.text(c["text"][:400] + "...")

    st.session_state.messages.append({"role": "assistant", "content": answer})
