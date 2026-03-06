"""
Storage module: save extracted invoices to SQLite and export to Excel.
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from models import Invoice

DB_PATH = "./invoices.db"
logger = logging.getLogger(__name__)


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            extracted_at    TEXT NOT NULL,
            source_file     TEXT,
            vendor_name     TEXT,
            invoice_number  TEXT,
            invoice_date    TEXT,
            due_date        TEXT,
            subtotal        REAL,
            tax             REAL,
            total           REAL,
            currency        TEXT,
            line_items_json TEXT,
            notes           TEXT,
            status          TEXT DEFAULT 'valid'
        )
    """)
    conn.commit()
    conn.close()


def save_invoice(invoice: Invoice, source_file: str | None = None) -> int:
    """Save a validated invoice to SQLite. Returns the new record ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """
        INSERT INTO invoices
            (extracted_at, source_file, vendor_name, invoice_number, invoice_date,
             due_date, subtotal, tax, total, currency, line_items_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            source_file,
            invoice.vendor_name,
            invoice.invoice_number,
            invoice.invoice_date,
            invoice.due_date,
            invoice.subtotal,
            invoice.tax,
            invoice.total,
            invoice.currency,
            json.dumps([item.model_dump() for item in invoice.line_items]),
            invoice.notes,
        ),
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info("Saved invoice #%d: %s, total %s %s", record_id, invoice.vendor_name, invoice.total, invoice.currency)
    return record_id


def get_all_invoices() -> pd.DataFrame:
    """Retrieve all invoices as a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM invoices ORDER BY id DESC", conn)
    conn.close()
    return df


def export_to_excel(output_path: str = "./invoices_export.xlsx") -> str:
    """Export all invoices to Excel and return the file path."""
    df = get_all_invoices()
    df.drop(columns=["line_items_json"], errors="ignore").to_excel(output_path, index=False)
    logger.info("Exported %d invoices to %s", len(df), output_path)
    return output_path
