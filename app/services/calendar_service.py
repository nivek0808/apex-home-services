"""Calendar service for booking appointment slots.

Supports both real Cal.com integration and mock fallback mode.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def book_slot(
    customer_name: str,
    phone: str,
    preferred_date: str,
    preferred_time: str,
    duration_hours: int = 2,
) -> dict:
    """Book a 2-hour appointment window.

    Returns dict with:
      - booking_url: URL for the customer to confirm
      - start_time: ISO formatted start time
      - end_time: ISO formatted end time
      - status: 'booked' or 'mock_booked'
    Falls back to mock booking if Cal.com is unavailable.
    """
    # Parse preferred date/time
    try:
        start_dt = datetime.strptime(f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        start_dt = datetime.now() + timedelta(days=1)

    end_dt = start_dt + timedelta(hours=duration_hours)
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # Try real Cal.com booking
    try:
        payload = {
            "eventTypeId": 1,
            "start": start_iso,
            "end": end_iso,
            "responses": {
                "name": customer_name,
                "email": "",
                "metadata": {"phone": phone},
            },
            "metadata": {},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.CALCOM_API_URL}/bookings",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            booking_url = data.get("bookingUrl", "") or data.get("url", "")
            logger.info(f"Cal.com booking created: {booking_url}")
            return {
                "booking_url": booking_url,
                "start_time": start_iso,
                "end_time": end_iso,
                "status": "booked",
                "source": "calcom",
            }
    except Exception as e:
        logger.warning(f"Cal.com unavailable ({e}), using fallback mode")

    # Fallback mock booking
    booking_url = f"https://apex.local/booking/mock_{customer_name.lower().replace(' ', '_')}"
    logger.info(f"Mock booking created: {booking_url}")
    return {
        "booking_url": booking_url,
        "start_time": start_iso,
        "end_time": end_iso,
        "status": "mock_booked",
        "source": "fallback",
    }


async def check_availability(date: str) -> dict:
    """Check available time slots for a given date.

    Returns dict with available_slots list and status.
    Falls back to mock availability.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{settings.CALCOM_API_URL}/availability",
                params={"date": date},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Cal.com availability check failed ({e}), using fallback")
        return {
            "available_slots": [
                "09:00", "11:00", "13:00", "15:00", "17:00"
            ],
            "status": "mock_available",
            "source": "fallback",
        }