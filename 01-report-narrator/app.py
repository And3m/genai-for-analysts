"""
Automated Report Narrator — Streamlit App
Entry point: streamlit run app.py
"""

import streamlit as st
from narrator import generate_narrative_stream
from data_loader import load_file, compute_stats

st.set_page_config(page_title="Report Narrator", page_icon="📊", layout="wide")

st.title("Automated Report Narrator")
st.caption("Upload a dataset → get a business-ready written summary powered by Claude.")

# --- Session state ---
if "narrative" not in st.session_state:
    st.session_state.narrative = None
if "last_file_name" not in st.session_state:
    st.session_state.last_file_name = None

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    tone = st.selectbox("Narrative tone", ["Executive summary", "Detailed analyst", "Casual update"])
    max_words = st.slider("Max words", min_value=100, max_value=600, value=300, step=50)
    generate_btn = st.button("Generate Narrative", type="primary")

# Clear saved narrative when a new file is uploaded
if uploaded_file is not None and uploaded_file.name != st.session_state.last_file_name:
    st.session_state.narrative = None
    st.session_state.last_file_name = uploaded_file.name

# --- Main area ---
if uploaded_file is None:
    st.info("Upload a CSV or Excel file using the sidebar to get started.")
    with st.expander("Try the sample dataset"):
        st.markdown("Use `sample_data/sales_summary.csv` — regional sales data across Jan–Mar 2024.")
    st.stop()

# Load data and show preview
df = load_file(uploaded_file)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Data Preview")
    st.dataframe(df.head(10), use_container_width=True)
with col2:
    st.metric("Rows", len(df))
    st.metric("Columns", len(df.columns))

# Compute stats once; show in expander
stats = compute_stats(df)
with st.expander("Computed Statistics"):
    st.json(stats)

# --- Generate (streaming) ---
if generate_btn:
    st.session_state.narrative = None
    st.subheader("Generated Narrative")
    try:
        streamed = st.write_stream(
            generate_narrative_stream(stats, tone=tone, max_words=max_words)
        )
        st.session_state.narrative = streamed
    except Exception as e:
        err = str(e)
        if "credit balance is too low" in err or "402" in err:
            st.error(
                "Anthropic API credit balance is too low. "
                "Please add credits at **console.anthropic.com → Plans & Billing**, then try again."
            )
        elif "401" in err or "authentication" in err.lower():
            st.error("Invalid API key. Check your `.env` file and restart the app.")
        else:
            st.error(f"API error: {e}")

# --- Show persisted narrative on subsequent reruns ---
elif st.session_state.narrative:
    st.subheader("Generated Narrative")
    st.markdown(st.session_state.narrative)

# --- Download (shown any time we have output) ---
if st.session_state.narrative:
    st.download_button(
        label="Download as .txt",
        data=st.session_state.narrative,
        file_name="report_narrative.txt",
        mime="text/plain",
    )
