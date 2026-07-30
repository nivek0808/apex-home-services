"""Google AI Studio LLM service for Apex Home Services.

Uses Google's Gemini and Gemma models via Google AI Studio API.
Implements model fallback and rate-limit cooldown when free tier limits are hit.
"""

import json
import logging
import re
import time
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Google AI Studio API endpoint
GOOGLE_AI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# Rate limit cooldown tracker
_last_rate_limit_time: float = 0
_last_model_switch: str = settings.GOOGLE_AI_MODEL_PRIMARY


def _get_headers() -> dict:
    """Return headers for Google AI API calls."""
    return {
        "Content-Type": "application/json",
    }


def _strip_markdown_json(text: str) -> str:
    """Strip markdown code block markers from LLM response.
    
    LLMs often wrap JSON in ```json ... ``` blocks.
    This strips those markers so json.loads() works.
    """
    if not text:
        return text
    
    # Match ```json ... ``` or ``` ... ``` patterns
    markdown_pattern = r'^```(?:json)?\s*(.*?)\s*```$'
    match = re.match(markdown_pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text


def _should_cooldown(model: str) -> bool:
    """Check if we need to cooldown due to rate limits."""
    global _last_rate_limit_time
    elapsed = time.time() - _last_rate_limit_time
    if elapsed < settings.GOOGLE_AI_COOLDOWN_SECONDS:
        remaining = settings.GOOGLE_AI_COOLDOWN_SECONDS - elapsed
        logger.warning(f"Rate limit cooldown active: {remaining:.0f}s remaining for {model}")
        return True
    return False


def _record_rate_limit():
    """Record that we hit a rate limit."""
    global _last_rate_limit_time
    _last_rate_limit_time = time.time()


def _get_model_to_use() -> str:
    """Get the model to use based on current state and fallback logic."""
    global _last_model_switch
    if _last_model_switch == settings.GOOGLE_AI_MODEL_PRIMARY:
        _last_model_switch = settings.GOOGLE_AI_MODEL_FALLBACK
    else:
        _last_model_switch = settings.GOOGLE_AI_MODEL_PRIMARY
    logger.info(f"Switching to fallback model: {_last_model_switch}")
    return _last_model_switch


async def _google_ai_completion(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> Optional[str]:
    """Make a chat completion call to Google AI Studio (Gemini/Gemma).

    Implements automatic fallback: if primary model hits rate limits (429),
    switches to fallback model after cooldown period.

    Args:
        messages: List of {role, content} dicts.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.

    Returns:
        The model's text response, or None on failure.
    """
    global _last_model_switch

    if not settings.GOOGLE_AI_API_KEY.strip():
        logger.warning("Google AI API key not configured")
        return None

    # Convert our message format to Google AI's format
    system_instruction = None
    contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})

    api_key = settings.GOOGLE_AI_API_KEY.strip()
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

    # Try primary model first, fallback to secondary if rate-limited
    models_to_try = [settings.GOOGLE_AI_MODEL_PRIMARY, settings.GOOGLE_AI_MODEL_FALLBACK]
    last_error = None

    for model in models_to_try:
        if _should_cooldown(model):
            continue

        url = f"{GOOGLE_AI_URL.format(model=model)}?key={api_key}"

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, headers=_get_headers(), json=payload)

                # Handle rate limiting specifically
                if resp.status_code == 429:
                    logger.warning(f"Rate limit hit for {model}, recording cooldown")
                    _record_rate_limit()
                    last_error = resp.json()
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Extract text from the response
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.error(f"No candidates in Google AI response for {model}")
                    continue

                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                text = part.get("text")
                if text:
                    logger.info(f"Success with {model}")
                    _last_model_switch = model
                    return text

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit for {model}, recording cooldown")
                _record_rate_limit()
                last_error = e.response.text
                continue
            logger.error(f"Google AI HTTP error for {model}: {e.response.status_code} - {e.response.text[:200]}")
            last_error = e.response.text
        except Exception as e:
            logger.error(f"Google AI call failed for {model}: {e}")
            last_error = str(e)

    # All models failed
    logger.error(f"All Google AI models failed. Last error: {last_error}")
    return None


async def _safe_json_parse(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    if not text:
        return None
    
    # Strip markdown code block markers
    cleaned = _strip_markdown_json(text)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed even after stripping markers: {e}")
        return None


async def extract_lead_from_transcript(transcript: str) -> dict:
    """Extract structured lead data from a call transcript.

    Returns dict with: customer_name, phone, address, issue_description, is_emergency.
    Falls back to mock data if LLM is unavailable.
    """
    system_prompt = (
        "You are an intelligent dispatcher for Apex Home Services. Extract the following fields "
        "from the call transcript and return ONLY valid JSON with these exact keys: "
        "customer_name, phone, address, issue_description, is_emergency. "
        "If a field is missing, use null. "
        "is_emergency should be true if the issue involves immediate danger "
        "like gas leak, fire, flood, pipe burst, or medical emergency."
    )
    result = await _google_ai_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript},
    ])

    if result:
        parsed = await _safe_json_parse(result)
        if parsed:
            # Normalize keys to match expected format
            return {
                "customer_name": parsed.get("customer_name") or parsed.get("name", "Unknown"),
                "phone": parsed.get("phone", "unknown"),
                "address": parsed.get("address", "unknown"),
                "issue_description": parsed.get("issue_description", transcript[:200] if transcript else "No transcript"),
                "is_emergency": bool(parsed.get("is_emergency", False)),
            }

    logger.warning("Google AI unavailable for lead extraction, using fallback")
    return _fallback_lead(transcript)


async def parse_vendor_invoice_text(raw_text: str) -> dict:
    """Parse vendor invoice text into structured data.

    Returns dict with: vendor_name, invoice_date, total_amount, line_items.
    Falls back to mock data if LLM is unavailable.
    """
    system_prompt = (
        "You are an invoice parsing assistant. Extract the following from the invoice text "
        "and return ONLY valid JSON with these exact keys: "
        "vendor_name, invoice_date (YYYY-MM-DD format), "
        "total_amount (string with currency symbol), "
        "line_items (array of objects with description, quantity, unit_price, total). "
        "If the text doesn't look like an invoice, return empty line_items array."
    )
    result = await _google_ai_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text},
    ])

    if result:
        parsed = await _safe_json_parse(result)
        if parsed:
            return parsed

    logger.warning("Google AI unavailable for invoice parsing, using fallback")
    return {
        "vendor_name": "Unknown Vendor",
        "invoice_date": "2026-07-30",
        "total_amount": "$0.00",
        "line_items": [],
    }


async def generate_sms_response(customer_message: str, lead_context: dict) -> str:
    """Generate a professional auto-reply SMS.

    Returns a concise, professional SMS text (under 160 chars).
    Falls back to a default message if LLM is unavailable.
    """
    system_prompt = (
        "You are an Apex Home Services customer support agent. "
        "Reply to the customer's message professionally and concisely "
        "(under 160 characters for SMS). "
        "Be friendly, helpful, and reference the lead context when relevant. "
        "Never include placeholder text — always provide a real response."
    )
    user_content = f"Customer message: {customer_message}\nLead context: {json.dumps(lead_context)}"

    result = await _google_ai_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=100,
    )

    if result and len(result.strip()) <= 160:
        return result.strip()

    logger.warning("Google AI SMS response too long or unavailable, using fallback")
    return (
        "Thanks for reaching out to Apex Home Services! "
        "We've received your message and will follow up shortly. "
        "For emergencies, call (555) 123-4567."
    )


def _fallback_lead(transcript: str) -> dict:
    """Fallback for when Google AI is unavailable."""
    # Try simple keyword extraction as a basic fallback
    is_emergency = any(
        kw in transcript.lower()
        for kw in ["emergency", "flood", "burst", "fire", "gas", "leaking", "flooding", "now"]
    )
    return {
        "customer_name": "Unknown",
        "phone": "unknown",
        "address": "unknown",
        "issue_description": transcript[:200] if transcript else "No transcript available",
        "is_emergency": is_emergency,
    }
