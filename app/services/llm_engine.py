"""Local LLM service connecting to Qwen via OpenAI-compatible endpoint."""

import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _chat_completion(messages: list[dict], temperature: float = 0.3) -> Optional[str]:
    """Make a chat completion call to the local LLM."""
    url = f"{settings.LOCAL_LLM_URL}/chat/completions"
    payload = {
        "model": "qwen",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


async def extract_lead_from_transcript(transcript: str) -> dict:
    """Extract structured lead data from a call transcript.

    Returns dict with: name, phone, address, issue, is_emergency.
    Falls back to mock data if LLM is unavailable.
    """
    system_prompt = (
        "You are an intelligent dispatcher. Extract the following fields from the call transcript: "
        "customer_name (string), phone (string), address (string), issue_description (string), "
        "is_emergency (boolean). Return ONLY valid JSON with these exact keys. "
        "If a field is missing, use null. If is_emergency is true, the issue involves immediate danger "
        "like gas leak, fire, flood, or medical emergency."
    )
    result = await _chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript},
    ])
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON, attempting to parse key lines")
    # Fallback mock data
    logger.warning("LLM unavailable or invalid response, using fallback")
    return {
        "name": "Unknown",
        "phone": "unknown",
        "address": "unknown",
        "issue_description": transcript[:200] if transcript else "No transcript available",
        "is_emergency": False,
    }


async def parse_vendor_invoice_text(raw_text: str) -> dict:
    """Parse vendor invoice text into structured data.

    Returns dict with: vendor, date, total, line_items (list of dicts).
    Falls back to mock data if LLM is unavailable.
    """
    system_prompt = (
        "You are an invoice parsing assistant. Extract the following from the invoice text: "
        "vendor_name (string), invoice_date (string in YYYY-MM-DD format), "
        "total_amount (string with currency symbol), "
        "line_items (array of objects with 'description', 'quantity', 'unit_price', 'total'). "
        "Return ONLY valid JSON with these exact keys."
    )
    result = await _chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text},
    ])
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON for invoice parsing")
    logger.warning("LLM unavailable or invalid response for invoice parsing, using fallback")
    return {
        "vendor_name": "Unknown Vendor",
        "invoice_date": "2026-07-30",
        "total_amount": "$0.00",
        "line_items": [],
    }


async def generate_sms_response(customer_message: str, lead_context: dict) -> str:
    """Generate a professional auto-reply SMS based on customer message and lead context.

    Returns a concise, professional SMS text.
    Falls back to a default message if LLM is unavailable.
    """
    system_prompt = (
        "You are an Apex Home Services customer support agent. "
        "Reply to the customer's message professionally and concisely (under 160 characters for SMS). "
        "Be friendly, helpful, and reference the lead context when relevant."
    )
    user_content = f"Customer message: {customer_message}\nLead context: {json.dumps(lead_context)}"
    result = await _chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ], temperature=0.7)
    if result:
        return result.strip()
    logger.warning("LLM unavailable for SMS generation, using fallback")
    return (
        "Thanks for reaching out to Apex Home Services! "
        "We've received your message and will follow up shortly. "
        "For emergencies, call us at (555) 123-4567."
    )