"""
Multi-Source Research Agent — Streamlit UI
Entry point: streamlit run app.py
"""

import streamlit as st
from agent import run_research_agent

st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")
st.title("Multi-Source Research Agent")
st.caption("Enter a business question. The agent searches the web, synthesises sources, and produces a structured research brief.")

SAMPLE_QUESTIONS = [
    "What is the competitive landscape for EV charging infrastructure in India?",
    "What are the main regulatory risks for fintech lending in Southeast Asia?",
    "Summarise recent enterprise AI adoption trends in healthcare.",
    "What are the top supply chain risks for semiconductor manufacturers in 2024?",
]

with st.sidebar:
    st.subheader("Sample questions")
    for q in SAMPLE_QUESTIONS:
        if st.button(q[:60] + "...", use_container_width=True, key=q):
            st.session_state["prefill"] = q

prefill = st.session_state.pop("prefill", "")
question = st.text_area("Research question:", value=prefill, height=80,
                          placeholder="e.g. What is the competitive landscape for...")
run_btn = st.button("Run Research Agent", type="primary")

if run_btn and question:
    status_placeholder = st.empty()
    steps_log = []

    def update_status(msg: str):
        steps_log.append(msg)
        status_placeholder.info(f"**Agent:** {msg}")

    with st.spinner("Research agent running..."):
        result = run_research_agent(question, progress_callback=update_status)

    status_placeholder.empty()

    brief = result.get("brief")
    if brief:
        st.subheader("Research Brief")

        st.markdown("### Executive Summary")
        st.markdown(brief.get("executive_summary", ""))

        st.markdown("### Key Findings")
        for finding in brief.get("key_findings", []):
            st.markdown(f"- {finding}")

        st.markdown("### Sources")
        for src in brief.get("sources", []):
            st.markdown(f"- {src}")

        gaps = brief.get("knowledge_gaps", [])
        if gaps:
            st.markdown("### Knowledge Gaps")
            for gap in gaps:
                st.markdown(f"- {gap}")

        # Export as markdown
        md_output = f"# Research Brief\n\n**Question:** {question}\n\n"
        md_output += f"## Executive Summary\n{brief.get('executive_summary', '')}\n\n"
        md_output += "## Key Findings\n" + "\n".join(f"- {f}" for f in brief.get("key_findings", [])) + "\n\n"
        md_output += "## Sources\n" + "\n".join(f"- {s}" for s in brief.get("sources", [])) + "\n"
        st.download_button("Download brief as Markdown", data=md_output, file_name="research_brief.md", mime="text/markdown")

    else:
        st.warning("Agent did not produce a structured brief. See tool log below.")

    with st.expander("Agent activity log"):
        for i, step in enumerate(steps_log):
            st.markdown(f"{i+1}. {step}")
        st.metric("Total iterations", result["iterations"])
