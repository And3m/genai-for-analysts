"""
Invoice / Document Intelligence Pipeline — Streamlit App
Entry point: streamlit run app.py
"""

import os
import tempfile
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from extractor import extract_invoice
from storage import init_db, save_invoice, get_all_invoices, export_to_excel

load_dotenv()
init_db()

st.set_page_config(page_title="Document Intelligence", page_icon="🧾", layout="wide")
st.title("Invoice / Document Intelligence Pipeline")
st.caption("Upload an invoice image or PDF — Claude Vision extracts structured data, validates it, and stores it.")

tab1, tab2 = st.tabs(["Extract Invoice", "Extracted Records"])

with tab1:
    uploaded = st.file_uploader("Upload invoice (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded and st.button("Extract Data", type="primary"):
        # Save upload to a temp file
        suffix = "." + uploaded.name.rsplit(".", 1)[-1].lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        with st.spinner("Sending to Claude Vision for extraction..."):
            invoice, error, raw_data = extract_invoice(tmp_path)

        os.unlink(tmp_path)

        if error:
            st.error(f"Extraction failed: {error}")
            with st.expander("Raw LLM output"):
                st.json(raw_data)
        else:
            st.success("Invoice extracted and validated successfully!")

            col1, col2, col3 = st.columns(3)
            col1.metric("Vendor", invoice.vendor_name)
            col2.metric("Total", f"{invoice.total:,.2f} {invoice.currency}")
            col3.metric("Date", invoice.invoice_date or "—")

            if invoice.line_items:
                st.subheader("Line Items")
                line_df = pd.DataFrame([item.model_dump() for item in invoice.line_items])
                st.dataframe(line_df, use_container_width=True, hide_index=True)

            record_id = save_invoice(invoice, source_file=uploaded.name)
            st.info(f"Saved as record #{record_id}")

            with st.expander("Full extracted data"):
                st.json(invoice.model_dump())

with tab2:
    df = get_all_invoices()

    if df.empty:
        st.info("No records yet. Extract an invoice in the first tab.")
    else:
        st.subheader(f"{len(df)} extracted invoice(s)")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total records", len(df))
        col2.metric("Total value", f"{df['total'].sum():,.2f}")
        col3.metric("Unique vendors", df["vendor_name"].nunique())

        st.dataframe(
            df[["id", "extracted_at", "vendor_name", "invoice_number", "invoice_date", "total", "currency", "source_file"]],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("Export to Excel"):
            path = export_to_excel()
            with open(path, "rb") as f:
                st.download_button(
                    "Download Excel file",
                    data=f,
                    file_name="invoices_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
