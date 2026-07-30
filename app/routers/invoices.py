"""Invoice parsing and dashboard stats router."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal, get_db
from app.models import Lead, Invoice, CallLog
from app.services import llm_engine, invoice_ninja_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invoices"])


class RawInvoiceRequest(BaseModel):
    raw_text: str


@router.post("/invoices/parse")
async def parse_invoice(raw_text: RawInvoiceRequest, db=Depends(get_db)):
    """Take raw invoice text/OCR string, call LLM parser, save to DB,
    and push invoice to Invoice Ninja API."""
    # Parse via LLM
    parsed = await llm_engine.parse_vendor_invoice_text(raw_text.raw_text)

    # Save to database
    invoice = Invoice(
        vendor_name=parsed.get("vendor_name", "Unknown"),
        invoice_date=parsed.get("invoice_date", ""),
        total_amount=parsed.get("total_amount", ""),
        raw_text=raw_text.raw_text,
        line_items_json=json.dumps(parsed.get("line_items", [])),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Push to Invoice Ninja
    ninja_status = None
    try:
        client_result = await invoice_ninja_client.create_client(
            name=parsed.get("vendor_name", "Unknown Vendor"),
            phone="unknown",
        )
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

    return {
        "parsed": parsed,
        "invoice_id": invoice.id,
        "ninja_status": ninja_status,
    }


@router.get("/dashboard/stats")
async def dashboard_stats(db=Depends(get_db)):
    """Return JSON summary of active leads, emergency counts,
    total invoiced, and integration statuses."""
    # Lead stats
    total_leads = db.query(Lead).count()
    active_leads = db.query(Lead).filter(Lead.status.in_(["new", "booked"])).count()
    emergency_count = db.query(Lead).filter(Lead.is_emergency == True).count()

    # Call log stats
    total_calls = db.query(CallLog).count()
    emergency_calls = db.query(CallLog).filter(CallLog.urgency == "emergency").count()

    # Invoice stats
    total_invoices = db.query(Invoice).count()
    total_invoiced_amount = 0
    for inv in db.query(Invoice).all():
        try:
            amount_str = inv.total_amount.replace("$", "").replace(",", "")
            total_invoiced_amount += float(amount_str)
        except (ValueError, AttributeError):
            pass

    # Integration health checks
    import httpx
    from app.config import settings

    integrations = {}

    # Google AI Studio (AI Assistant)
    ai_status = "healthy" if settings.google_ai_available else "unhealthy"
    integrations["google_ai"] = {
        "status": ai_status,
        "name": "AI Assistant",
        "description": f"Powered by {settings.GOOGLE_AI_MODEL_PRIMARY}",
    }

    # Invoice Ninja - quick connectivity check
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{invoice_ninja_client.settings.INVOICE_NINJA_URL}/",
                follow_redirects=False,
            )
            integrations["invoice_ninja"] = {
                "status": "healthy",
                "name": "Invoice Ninja",
                "description": "Invoice & billing management - Port 8003",
            }
    except Exception:
        integrations["invoice_ninja"] = {
            "status": "degraded",
            "name": "Invoice Ninja",
            "description": "Invoice & billing management - Port 8003",
        }

    # Cal.com - quick connectivity check
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            base_url = invoice_ninja_client.settings.CALCOM_API_URL.replace("/api/v1", "")
            resp = await client.get(base_url, follow_redirects=False)
            integrations["calcom"] = {
                "status": "healthy",
                "name": "Calendar",
                "description": "Appointment scheduling - Port 3000",
            }
    except Exception:
        integrations["calcom"] = {
            "status": "degraded",
            "name": "Calendar",
            "description": "Appointment scheduling - Port 3000",
        }

    # n8n - quick connectivity check
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:5678/", follow_redirects=True)
            if resp.status_code == 200:
                integrations["n8n"] = {
                    "status": "healthy",
                    "name": "n8n Automation",
                    "description": "Workflow automation hub - Port 5678",
                }
            else:
                integrations["n8n"] = {
                    "status": "degraded",
                    "name": "n8n Automation",
                    "description": "Workflow automation hub - Port 5678",
                }
    except Exception:
        integrations["n8n"] = {
            "status": "degraded",
            "name": "n8n Automation",
            "description": "Workflow automation hub - Port 5678",
        }

    return {
        "leads": {
            "total": total_leads,
            "active": active_leads,
            "emergency": emergency_count,
        },
        "calls": {
            "total": total_calls,
            "emergency_calls": emergency_calls,
        },
        "invoices": {
            "total": total_invoices,
            "total_amount": f"${total_invoiced_amount:.2f}",
        },
        "integrations": integrations,
    }
