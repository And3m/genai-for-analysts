"""
Prompt Engineering Playground — Streamlit App
Entry point: streamlit run app.py
"""

import time
import streamlit as st
import pandas as pd
from prompt_runner import run_technique, TECHNIQUES
from tasks import TASK_TEMPLATES

st.set_page_config(page_title="Prompt Playground", page_icon="🧪", layout="wide")

st.title("Prompt Engineering Playground")
st.caption("Compare zero-shot, few-shot, chain-of-thought, and role prompting side-by-side on real business tasks.")

# --- Sidebar ---
with st.sidebar:
    st.header("Task Setup")
    task_name = st.selectbox("Business task", list(TASK_TEMPLATES.keys()))
    task = TASK_TEMPLATES[task_name]
    st.caption(task["description"])

    st.divider()
    user_input = st.text_area("Input text to process", value=task["example_input"], height=150)

    st.divider()
    st.subheader("Techniques to compare")
    selected_techniques = []
    for t in TECHNIQUES:
        if st.checkbox(t, value=True):
            selected_techniques.append(t)

    run_btn = st.button("Run Comparison", type="primary", disabled=len(selected_techniques) == 0)

# --- Main area ---
if not run_btn:
    st.info("Configure a task and click **Run Comparison** to start.")
    st.stop()

results = []
progress = st.progress(0, text="Running techniques...")

for i, technique in enumerate(selected_techniques):
    with st.spinner(f"Running: {technique}"):
        start = time.time()
        output, tokens_used = run_technique(technique, task, user_input)
        latency = round(time.time() - start, 2)
        results.append({
            "Technique": technique,
            "Output": output,
            "Input tokens": tokens_used.get("input", 0),
            "Output tokens": tokens_used.get("output", 0),
            "Latency (s)": latency,
        })
    progress.progress((i + 1) / len(selected_techniques), text=f"Completed: {technique}")

progress.empty()

# Display results
st.subheader("Results")
for r in results:
    with st.expander(f"**{r['Technique']}** — {r['Output tokens']} output tokens | {r['Latency (s)']}s"):
        st.markdown(r["Output"])

# Summary table
st.subheader("Comparison Summary")
summary_df = pd.DataFrame([{k: v for k, v in r.items() if k != "Output"} for r in results])
st.dataframe(summary_df, use_container_width=True)

# Export
csv = pd.DataFrame(results).to_csv(index=False)
st.download_button("Export results to CSV", data=csv, file_name="prompt_comparison.csv", mime="text/csv")
