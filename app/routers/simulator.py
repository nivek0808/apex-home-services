"""Interactive simulator router for testing voice calls, SMS, and invoice parsing."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal, get_db
from app.models import Lead, Invoice, CallLog
from app.services import llm_engine, invoice_ninja_client, calendar_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


# --- Request/Response Models ---

class VoiceCallRequest(BaseModel):
    transcript: str


class VoiceCallResponse(BaseModel):
    lead: dict
    call_log: dict
    action_taken: str


class SMSRequest(BaseModel):
    customer_message: str
    lead_id: int | None = None


class SMSResponse(BaseModel):
    auto_reply: str
    lead_context: dict


class InvoiceParseRequest(BaseModel):
    raw_text: str


class InvoiceParseResponse(BaseModel):
    parsed: dict
    invoice_id: int | None
    ninja_status: str | None


class BookSlotRequest(BaseModel):
    lead_id: int
    preferred_date: str
    preferred_time: str


class BookSlotResponse(BaseModel):
    booking_url: str
    start_time: str
    end_time: str
    status: str


class SyncToNinjaRequest(BaseModel):
    lead_id: int


class SyncToNinjaResponse(BaseModel):
    client_id: str
    invoice_id: str | None
    status: str


# --- Endpoints ---

@router.post("/voice-call", response_model=VoiceCallResponse)
async def simulate_voice_call(req: VoiceCallRequest, db=Depends(get_db)):
    """Simulate an after-hours emergency voice call.

    Processes the transcript through the LLM, creates a Lead and CallLog,
    and attempts auto-booking for emergencies.
    """
    # Extract lead data via LLM
    lead_data = await llm_engine.extract_lead_from_transcript(req.transcript)

    # Determine urgency
    is_emergency = lead_data.get("is_emergency", False)
    urgency = "emergency" if is_emergency else "normal"

    # Create CallLog
    call_log = CallLog(
        caller_number=lead_data.get("phone", "unknown"),
        transcript=req.transcript,
        extracted_intent=lead_data.get("issue_description", ""),
        urgency=urgency,
        summary=f"Lead: {lead_data.get('name', 'Unknown')}",
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)

    # Create Lead
    lead = Lead(
        customer_name=lead_data.get("name", "Unknown"),
        phone=lead_data.get("phone", "unknown"),
        address=lead_data.get("address", "unknown"),
        issue_description=lead_data.get("issue_description", ""),
        is_emergency=is_emergency,
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Auto-book if emergency
    action = "Call logged, lead created."
    if is_emergency:
        booking = await calendar_service.book_slot(
            customer_name=lead_data.get("name", "Unknown"),
            phone=lead_data.get("phone", "unknown"),
            preferred_date="2026-07-31",
            preferred_time="09:00",
        )
        action = f"EMERGENCY: Auto-booked. {booking['status']} - {booking['booking_url']}"

    return VoiceCallResponse(
        lead={
            "id": lead.id,
            "name": lead.customer_name,
            "phone": lead.phone,
            "address": lead.address,
            "issue": lead.issue_description,
            "is_emergency": lead.is_emergency,
            "status": lead.status,
        },
        call_log={
            "id": call_log.id,
            "caller": call_log.caller_number,
            "urgency": call_log.urgency,
            "summary": call_log.summary,
        },
        action_taken=action,
    )


@router.post("/sms", response_model=SMSResponse)
async def simulate_sms(req: SMSRequest, db=Depends(get_db)):
    """Simulate receiving an SMS and generating an auto-reply."""
    lead_context = {}
    if req.lead_id:
        lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
        if lead:
            lead_context = {
                "name": lead.customer_name,
                "issue": lead.issue_description,
                "status": lead.status,
            }

    auto_reply = await llm_engine.generate_sms_response(req.customer_message, lead_context)

    return SMSResponse(
        auto_reply=auto_reply,
        lead_context=lead_context,
    )


@router.post("/invoice-parse", response_model=InvoiceParseResponse)
async def simulate_invoice_parse(req: InvoiceParseRequest, db=Depends(get_db)):
    """Parse a raw invoice text via LLM, save to DB, and push to Invoice Ninja."""
    # Parse via LLM
    parsed = await llm_engine.parse_vendor_invoice_text(req.raw_text)

    # Save to database
    invoice = Invoice(
        vendor_name=parsed.get("vendor_name", "Unknown"),
        invoice_date=parsed.get("invoice_date", ""),
        total_amount=parsed.get("total_amount", ""),
        raw_text=req.raw_text,
        line_items_json=json.dumps(parsed.get("line_items", [])),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Push to Invoice Ninja
    ninja_status = None
    try:
        # Create client first
        client_result = await invoice_ninja_client.create_client(
            name=parsed.get("vendor_name", "Unknown Vendor"),
            phone="unknown",
        )
        # Then create invoice
        line_items = parsed.get("line_items", [])
        await invoice_ninja_client.create_invoice(
            client_id=client_result["client_id"],
            line_items=line_items,
            total=parsed.get("total_amount", "$0.00"),
            invoice_date=parsed.get("invoice_date", "2026-07-30"),
        )
        ninja_status = f"client={client_result['status']}, invoice=created"
    except Exception as e:
        ninja_status = f"error: {str(e)}"

    return InvoiceParseResponse(
        parsed=parsed,
        invoice_id=invoice.id,
        ninja_status=ninja_status,
    )


@router.post("/book-slot", response_model=BookSlotResponse)
async def simulate_book_slot(req: BookSlotRequest, db=Depends(get_db)):
    """Book an appointment slot for a given lead."""
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    booking = await calendar_service.book_slot(
        customer_name=lead.customer_name,
        phone=lead.phone,
        preferred_date=req.preferred_date,
        preferred_time=req.preferred_time,
    )

    lead.status = "booked"
    db.commit()

    return BookSlotResponse(
        booking_url=booking["booking_url"],
        start_time=booking["start_time"],
        end_time=booking["end_time"],
        status=booking["status"],
    )


@router.post("/sync-to-ninja", response_model=SyncToNinjaResponse)
async def simulate_sync_to_ninja(req: SyncToNinjaRequest, db=Depends(get_db)):
    """Sync a lead to Invoice Ninja (create client + invoice)."""
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    client_result = await invoice_ninja_client.create_client(
        name=lead.customer_name,
        phone=lead.phone,
        address=lead.address or "",
    )

    lead.invoice_ninja_client_id = client_result["client_id"]
    db.commit()

    return SyncToNinjaResponse(
        client_id=client_result["client_id"],
        invoice_id=None,
        status=client_result["status"],
    )