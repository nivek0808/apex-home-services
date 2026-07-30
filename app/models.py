"""Database models for Apex Home Services."""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from app.database import Base


class Lead(Base):
    """Represents an incoming customer lead."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone = Column(String, index=True)
    address = Column(String)
    issue_description = Column(Text)
    is_emergency = Column(Boolean, default=False)
    status = Column(String, default="new")  # new, booked, completed
    invoice_ninja_client_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Invoice(Base):
    """Represents a parsed vendor invoice."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, index=True)
    invoice_date = Column(String)
    total_amount = Column(String)
    raw_text = Column(Text)
    line_items_json = Column(Text)  # JSON string of line items
    invoice_ninja_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class CallLog(Base):
    """Represents a recorded/processed voice call."""
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    caller_number = Column(String, index=True)
    transcript = Column(Text)
    extracted_intent = Column(String)
    urgency = Column(String)  # low, medium, high, emergency
    summary = Column(Text)
    created_at = Column(DateTime, server_default=func.now())