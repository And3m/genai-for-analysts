"""
Data Analyst Agent — Streamlit UI
Entry point: streamlit run app.py
"""

import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Data Analyst Agent", page_icon="🤖", layout="wide")
st.title("Data Analyst Agent")
st.caption("Ask any question about the sales dataset in plain English. The agent writes and runs the analysis for you.")

SAMPLE_QUESTIONS = [
    "Which region had the highest total revenue?",
    "What are the top 3 products by return rate?",
    "Compare revenue across customer segments.",
    "Which month had the lowest sales?",
    "What is the average revenue per unit for each product?",
]

with st.sidebar:
    st.subheader("Sample questions")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state["prefill"] = q

prefill = st.session_state.pop("prefill", "")
user_question = st.text_input("Your question:", value=prefill, placeholder="e.g. Which region had the highest revenue growth?")
run_btn = st.button("Ask Agent", type="primary")

if run_btn and user_question:
    with st.spinner("Agent is working..."):
        result = run_agent(user_question)

    st.subheader("Answer")
    st.markdown(result["answer"])

    col1, col2 = st.columns(2)
    col1.metric("Agent iterations", result["iterations"])

    with st.expander("Tool call log"):
        for i, call in enumerate(result["tool_log"]):
            st.markdown(f"**Step {i+1}: `{call['tool']}`**")
            if call["tool"] == "query_database":
                st.code(call["input"].get("sql", ""), language="sql")
            else:
                st.code(call["input"].get("code", ""), language="python")
            st.text(f"Output (truncated): {call['output'][:300]}")
            st.divider()
