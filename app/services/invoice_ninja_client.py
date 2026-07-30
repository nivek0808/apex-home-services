"""Invoice Ninja v5 API client with graceful fallback mode."""

import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _get_headers() -> dict:
    """Return headers for Invoice Ninja API calls."""
    return {
        "X-Ninja-Token": settings.INVOICE_NINJA_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def create_client(name: str, phone: str, address: str = "") -> dict:
    """Create a new client in Invoice Ninja.

    Returns dict with 'client_id' (real or mock) and 'status'.
    Falls back to mock ID if Invoice Ninja is unavailable.
    """
    payload = {
        "data": {
            "type": "client",
            "attributes": {
                "name": name,
                "contact_name": name,
                "email": f"{name.lower().replace(' ', '.')}@example.com",
                "phone": phone,
                "address": address,
                "website": "",
            },
        }
    }
    try:
        headers = await _get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.INVOICE_NINJA_URL}/v5/clients",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            client_id = data.get("data", {}).get("id", "unknown")
            logger.info(f"Created Invoice Ninja client: {client_id}")
            return {"client_id": client_id, "status": "created", "source": "invoice_ninja"}
    except Exception as e:
        logger.warning(f"Invoice Ninja unavailable ({e}), using fallback mode")
        mock_id = f"mock_{name.lower().replace(' ', '_')}_{len(name)}"
        # Log the payload for later sync when service is back
        logger.info(f"Fallback client payload: {json.dumps(payload)}")
        return {"client_id": mock_id, "status": "mock_created", "source": "fallback"}


async def create_invoice(
    client_id: str,
    line_items: list[dict],
    total: str,
    invoice_date: str = "2026-07-30",
) -> dict:
    """Create an invoice in Invoice Ninja for the given client.

    Returns dict with 'invoice_id' (real or mock) and 'status'.
    Falls back to mock ID if Invoice Ninja is unavailable.
    """
    payload = {
        "data": {
            "type": "invoice",
            "attributes": {
                "client_id": client_id,
                "invoice_number": f"INV-{invoice_date.replace('-', '')}",
                "po_number": "",
                "date": invoice_date,
                "due_date": "2026-08-13",
                "line_items": line_items,
                "amount": total,
                "status_id": "1",
            },
        }
    }
    try:
        headers = await _get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.INVOICE_NINJA_URL}/v5/invoices",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            invoice_id = data.get("data", {}).get("id", "unknown")
            logger.info(f"Created Invoice Ninja invoice: {invoice_id}")
            return {"invoice_id": invoice_id, "status": "created", "source": "invoice_ninja"}
    except Exception as e:
        logger.warning(f"Invoice Ninja unavailable for invoice creation ({e}), using fallback")
        mock_id = f"mock_inv_{client_id}_{len(line_items)}"
        logger.info(f"Fallback invoice payload: {json.dumps(payload)}")
        return {"invoice_id": mock_id, "status": "mock_created", "source": "fallback"}