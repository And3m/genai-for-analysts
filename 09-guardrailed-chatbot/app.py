"""
Guardrailed Enterprise Chatbot — Streamlit UI
Entry point: streamlit run app.py
"""

import os
import uuid
import anthropic
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from guardrails import is_on_topic, detect_and_redact_pii, validate_output
from audit_logger import init_db, log_interaction, get_recent_logs

load_dotenv()
init_db()

st.set_page_config(page_title="Enterprise Chatbot", page_icon="🏢", layout="wide")
st.title("Guardrailed Enterprise HR Chatbot")
st.caption("An HR policy assistant with topic restriction, PII redaction, output validation, and audit logging.")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: guardrail status and audit log
with st.sidebar:
    st.subheader(f"Session: `{st.session_state.session_id}`")
    st.markdown("**Active guardrails:**")
    st.markdown("- Topic restriction (HR/policy only)")
    st.markdown("- PII detection & redaction in logs")
    st.markdown("- Output length validation")
    st.markdown("- Full audit logging")

    if st.button("View audit log"):
        st.session_state["show_audit"] = True

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("guardrail_info"):
            st.caption(msg["guardrail_info"])

# Chat input
user_input = st.chat_input("Ask about HR policies, leave, benefits, compliance...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # --- Guardrail 1: PII detection ---
    redacted_input, pii_types = detect_and_redact_pii(user_input)
    pii_warning = f"PII detected and redacted from logs: {', '.join(pii_types)}" if pii_types else None

    # --- Guardrail 2: Topic check ---
    topic_on = is_on_topic(user_input)

    if not topic_on:
        response_text = (
            "I'm configured to answer questions about HR policies, leave, benefits, "
            "payroll, and company compliance matters only. "
            "For other topics, please contact the relevant team directly."
        )
        log_interaction(
            session_id=st.session_state.session_id,
            user_input_raw=user_input,
            user_input_redacted=redacted_input,
            pii_types=pii_types,
            topic_verdict="OFF_TOPIC",
            llm_response=None,
            was_blocked=True,
            block_reason="Off-topic input",
        )
        guardrail_info = "Guardrail: OFF-TOPIC — request blocked"
    else:
        # --- LLM call ---
        llm_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You are an HR policy assistant for ACME Corp. "
                "Answer questions about company policies, leave, benefits, and compliance. "
                "Be precise and cite policy sections where possible. "
                "If you don't know the answer from the provided context, say so."
            ),
            messages=[{"role": "user", "content": user_input}],
        )
        raw_response = llm_response.content[0].text

        # --- Guardrail 3: Output validation ---
        is_valid, response_text = validate_output(raw_response)

        log_interaction(
            session_id=st.session_state.session_id,
            user_input_raw=user_input,
            user_input_redacted=redacted_input,
            pii_types=pii_types,
            topic_verdict="ON_TOPIC",
            llm_response=response_text,
            was_blocked=False,
        )

        guardrail_parts = []
        if pii_warning:
            guardrail_parts.append(pii_warning)
        if len(raw_response) > 3000:
            guardrail_parts.append("Output truncated by length guardrail")
        guardrail_info = " | ".join(guardrail_parts) if guardrail_parts else None

    with st.chat_message("assistant"):
        st.markdown(response_text)
        if guardrail_info:
            st.caption(f"Guardrail info: {guardrail_info}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "guardrail_info": guardrail_info,
    })

# Audit log viewer
if st.session_state.get("show_audit"):
    st.divider()
    st.subheader("Audit Log (last 50 interactions)")
    logs = get_recent_logs(50)
    if logs:
        log_df = pd.DataFrame(logs)
        st.dataframe(log_df[["timestamp", "session_id", "user_input_redacted", "topic_verdict",
                               "pii_types_detected", "was_blocked", "block_reason"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No interactions logged yet.")
    if st.button("Close audit log"):
        st.session_state["show_audit"] = False
        st.rerun()
