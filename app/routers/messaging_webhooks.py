"""SMS/Telegram/WhatsApp messaging webhook handler."""

import logging

from fastapi import APIRouter, Depends, Request

from app.database import SessionLocal, get_db
from app.models import Lead
from app.services import llm_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/messaging", tags=["messaging-webhooks"])


@router.post("/")
async def handle_messaging_webhook(request: Request, db=Depends(get_db)):
    """Handle incoming messaging webhooks (SMS/Telegram/WhatsApp).

    Parses intent via local LLM and returns auto-responder text.
    Supports multiple webhook formats.
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON payload"}

    # Extract message and sender (handle multiple webhook formats)
    message = (
        body.get("message", body.get("text", body.get("content", "")))
    )
    sender = (
        body.get("from", body.get("sender", body.get("fromPhoneNumber", "unknown")))
    )
    platform = body.get("platform", body.get("source", "unknown"))

    if not message:
        return {"status": "skipped", "message": "No message content"}

    # Try to find matching lead by phone
    lead_context = {}
    if sender != "unknown":
        lead = db.query(Lead).filter(Lead.phone == sender).order_by(Lead.id.desc()).first()
        if lead:
            lead_context = {
                "name": lead.customer_name,
                "issue": lead.issue_description,
                "status": lead.status,
                "lead_id": lead.id,
            }

    # Generate auto-reply via LLM
    auto_reply = await llm_engine.generate_sms_response(message, lead_context)

    return {
        "status": "processed",
        "platform": platform,
        "sender": sender,
        "message": message,
        "lead_context": lead_context,
        "auto_reply": auto_reply,
    }


@router.post("/telegram")
async def handle_telegram_webhook(request: Request, db=Depends(get_db)):
    """Specific Telegram webhook handler."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    # Telegram format
    message = body.get("message", {}).get("text", "")
    chat_id = body.get("message", {}).get("chat", {}).get("id", "")
    from_name = body.get("message", {}).get("from", {}).get("first_name", "user")

    if not message:
        return {"status": "skipped", "message": "No message"}

    lead_context = {}
    auto_reply = await llm_engine.generate_sms_response(message, lead_context)

    return {
        "status": "processed",
        "chat_id": chat_id,
        "from": from_name,
        "auto_reply": auto_reply,
    }