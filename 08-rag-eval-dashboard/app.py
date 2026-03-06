"""
RAG Evaluation Dashboard — Streamlit + Plotly
Entry point: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

RESULTS_PATH = "./results.csv"
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

st.set_page_config(page_title="RAG Eval Dashboard", page_icon="📊", layout="wide")
st.title("RAG Evaluation Dashboard")
st.caption("Measure and explore RAG pipeline quality: faithfulness, answer relevance, context precision and recall.")

# Load results
if not os.path.exists(RESULTS_PATH):
    st.warning(f"No results file found at `{RESULTS_PATH}`. Run `eval_runner.py` first.")
    st.stop()

df = pd.read_csv(RESULTS_PATH)
available_metrics = [m for m in METRICS if m in df.columns]

if not available_metrics:
    st.error("No RAGAS metric columns found in results. Re-run eval_runner.py with RAGAS installed.")
    st.stop()

# --- Summary metrics ---
st.subheader("Overall Performance")
cols = st.columns(len(available_metrics))
for col, metric in zip(cols, available_metrics):
    mean_val = df[metric].mean()
    col.metric(metric.replace("_", " ").title(), f"{mean_val:.3f}", help=f"Mean {metric} across all questions")

st.divider()

# --- Score distribution ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Score Distribution")
    fig_box = go.Figure()
    for metric in available_metrics:
        fig_box.add_trace(go.Box(y=df[metric], name=metric.replace("_", " ").title()))
    fig_box.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    st.subheader("Metric Radar (Mean Scores)")
    values = [df[m].mean() for m in available_metrics]
    fig_radar = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=[m.replace("_", " ").title() for m in available_metrics] + [available_metrics[0].replace("_", " ").title()],
        fill="toself",
        name="RAG Pipeline",
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
    st.plotly_chart(fig_radar, use_container_width=True)

# --- Per-question breakdown ---
st.subheader("Per-Question Breakdown")
metric_filter = st.selectbox("Sort by metric", available_metrics)
sorted_df = df.sort_values(metric_filter, ascending=True)

fig_bar = px.bar(
    sorted_df,
    x=metric_filter,
    y="question",
    orientation="h",
    color=metric_filter,
    color_continuous_scale="RdYlGn",
    range_color=[0, 1],
    labels={"question": ""},
    height=max(400, len(df) * 40),
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Low-scoring questions ---
threshold = st.slider("Flag questions below score", 0.0, 1.0, 0.5, 0.05)
low_df = df[df[available_metrics].min(axis=1) < threshold]
if not low_df.empty:
    st.subheader(f"Questions with at least one metric below {threshold}")
    st.dataframe(
        low_df[["question", "answer"] + available_metrics],
        use_container_width=True,
        hide_index=True,
    )

# --- Raw data ---
with st.expander("Full results table"):
    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", df.to_csv(index=False), "rag_eval_results.csv", "text/csv")
