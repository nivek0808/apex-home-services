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

    integrations = {}

    # Local LLM
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{llm_engine.settings.LOCAL_LLM_URL}/models")
            integrations["local_llm"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "url": llm_engine.settings.LOCAL_LLM_URL,
            }
    except Exception:
        integrations["local_llm"] = {
            "status": "unhealthy",
            "url": llm_engine.settings.LOCAL_LLM_URL,
        }

    # Invoice Ninja
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"X-Ninja-Token": invoice_ninja_client.settings.INVOICE_NINJA_TOKEN}
            resp = await client.get(
                f"{invoice_ninja_client.settings.INVOICE_NINJA_URL}/v5/clients",
                headers=headers,
            )
            integrations["invoice_ninja"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "url": invoice_ninja_client.settings.INVOICE_NINJA_URL,
            }
    except Exception:
        integrations["invoice_ninja"] = {
            "status": "unhealthy",
            "url": invoice_ninja_client.settings.INVOICE_NINJA_URL,
        }

    # Cal.com
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{invoice_ninja_client.settings.CALCOM_API_URL}/health")
            integrations["calcom"] = {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "url": invoice_ninja_client.settings.CALCOM_API_URL,
            }
    except Exception:
        integrations["calcom"] = {
            "status": "unhealthy",
            "url": invoice_ninja_client.settings.CALCOM_API_URL,
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