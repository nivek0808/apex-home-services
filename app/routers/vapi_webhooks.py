"""Vapi.ai webhook handler for voice call end-of-call reports."""

import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.database import SessionLocal, get_db
from app.models import Lead, CallLog
from app.services import llm_engine, calendar_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/vapi", tags=["vapi-webhooks"])


class VapiEndOfCallWebhook(BaseModel):
    """Simplified Vapi.ai end-of-call webhook payload."""
    call_id: str
    customer_phone: str | None = None
    transcript: str
    status: str


@router.post("/")
async def handle_vapi_webhook(request: Request, db=Depends(get_db)):
    """Handle Vapi.ai end-of-call report webhook.

    Passes transcript to LLM, creates CallLog and Lead,
    and attempts auto-booking if emergency.
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON payload"}

    # Extract fields (handle both simplified and full Vapi payload)
    transcript = body.get("transcript", body.get("customerTranscription", ""))
    caller = body.get("customerPhoneNumber", body.get("customer_phone", "unknown"))
    call_id = body.get("callId", body.get("call_id", "unknown"))

    if not transcript:
        return {"status": "skipped", "message": "No transcript available"}

    # Extract lead data via LLM
    lead_data = await llm_engine.extract_lead_from_transcript(transcript)

    # Determine urgency
    is_emergency = lead_data.get("is_emergency", False)
    urgency = "emergency" if is_emergency else "normal"

    # Create CallLog
    call_log = CallLog(
        caller_number=caller,
        transcript=transcript,
        extracted_intent=lead_data.get("issue_description", ""),
        urgency=urgency,
        summary=f"Vapi call {call_id}: {lead_data.get('name', 'Unknown')}",
    )
    db.add(call_log)

    # Create Lead
    lead = Lead(
        customer_name=lead_data.get("name", "Unknown"),
        phone=lead_data.get("phone", caller),
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
            phone=lead_data.get("phone", caller),
            preferred_date="2026-07-31",
            preferred_time="09:00",
        )
        lead.status = "booked"
        db.commit()
        action = f"EMERGENCY: Auto-booked. {booking['status']} - {booking['booking_url']}"

    return {
        "status": "processed",
        "call_id": call_id,
        "lead_id": lead.id,
        "call_log_id": call_log.id,
        "is_emergency": is_emergency,
        "action": action,
    }