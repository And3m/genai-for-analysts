"""
Pydantic models for invoice/document structured extraction.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float


class Invoice(BaseModel):
    vendor_name: str = Field(..., description="Name of the vendor or supplier")
    invoice_number: Optional[str] = Field(None, description="Invoice or reference number")
    invoice_date: Optional[str] = Field(None, description="Date of the invoice (YYYY-MM-DD if possible)")
    due_date: Optional[str] = Field(None, description="Payment due date")
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: float = Field(..., description="Total amount due")
    currency: str = Field(default="USD", description="Currency code, e.g. USD, AUD, GBP")
    notes: Optional[str] = None

    @field_validator("total")
    @classmethod
    def total_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Total must be greater than zero")
        return v
