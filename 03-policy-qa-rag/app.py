"""
Policy Q&A Bot — Streamlit Chat UI
Entry point: streamlit run app.py
"""

import os
import anthropic
import streamlit as st
from dotenv import load_dotenv
from retriever import retrieve

load_dotenv()

st.set_page_config(page_title="Policy Q&A Bot", page_icon="📋", layout="wide")
st.title("Policy / SOP Q&A Bot")
st.caption("Ask questions about your company documents. Answers are grounded in the uploaded policies with source citations.")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Session state for chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat input ---
user_query = st.chat_input("Ask a question about your policies...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Retrieve relevant chunks
    with st.spinner("Searching documents..."):
        chunks = retrieve(user_query)

    context_block = "\n\n---\n\n".join(
        f"[Source: {c['source']}, chunk {c['chunk_index']}]\n{c['text']}" for c in chunks
    )

    system_prompt = (
        "You are a helpful HR and compliance assistant. "
        "Answer questions based ONLY on the provided policy documents. "
        "If the answer is not in the documents, say so clearly. "
        "Always cite the source document at the end of your answer."
    )

    messages_for_api = [
        {"role": "user", "content": f"Context from company documents:\n\n{context_block}\n\n---\n\nQuestion: {user_query}"}
    ]

    with st.chat_message("assistant"):
        with st.spinner("Generating answer..."):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=messages_for_api,
            )
            answer = response.content[0].text
            st.markdown(answer)

            with st.expander("Retrieved source chunks"):
                for c in chunks:
                    st.markdown(f"**{c['source']}** (chunk {c['chunk_index']})")
                    st.text(c["text"][:300] + "...")

    st.session_state.messages.append({"role": "assistant", "content": answer})
