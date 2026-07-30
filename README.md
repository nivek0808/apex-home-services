# Apex Home Services - Full-Stack Automation Sandbox

A sandbox application for simulating and testing the full automation stack for **Apex Home Services** (or any SMB home services business). This system mirrors the intended production architecture using **local LLMs** and **graceful fallback modes** for all commercial services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dashboard (HTML)                         │
│              http://localhost:8000/                             │
├─────────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                             │
│              http://localhost:8000/docs                         │
├──────────┬──────────────┬───────────────┬───────────────────────┤
│  Voice   │    SMS       │    Invoice    │      Calendar         │
│  (Vapi)  │  (Telegram)  │   (Ninja API) │    (Cal.com)          │
├──────────┴──────────────┴───────────────┴───────────────────────┤
│              Local LLM (Qwen via Ollama)                        │
│              http://localhost:8080                              │
├─────────────────────────────────────────────────────────────────┤
│              SQLite Database (leads, invoices, calls)           │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Ollama running Qwen model (optional, for full LLM features)
- Invoice Ninja v5 (optional)
- Cal.com (optional)

### 2. Install Dependencies

```bash
cd aiClientSupport
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your service URLs and tokens
```

### 4. Run

```bash
./run.sh
```

Or manually:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open Dashboard

Navigate to **http://localhost:8000/** to access the interactive dashboard.

## Features

### Voice Call Simulator
- Paste a call transcript and simulate after-hours emergency call processing
- LLM extracts customer name, phone, address, issue, and urgency
- Auto-books emergency appointments
- Creates CallLog and Lead records

### SMS Auto-Responder
- Simulate receiving customer SMS messages
- LLM generates professional auto-replies with context awareness
- Links to existing leads by phone number

### Invoice Parser
- Paste raw invoice text or OCR output
- LLM extracts vendor, date, total, and line items
- Saves to database and pushes to Invoice Ninja

### Appointment Booking
- Book 2-hour appointment windows
- Integrates with Cal.com (or uses mock booking)
- Returns booking confirmation URLs

### Dashboard Stats
- Real-time counts: leads, calls, invoices, emergencies
- Integration health checks for LLM, Invoice Ninja, and Cal.com

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| POST | `/api/simulator/voice-call` | Simulate voice call |
| POST | `/api/simulator/sms` | Simulate SMS |
| POST | `/api/simulator/invoice-parse` | Parse invoice |
| POST | `/api/simulator/book-slot` | Book appointment |
| POST | `/api/simulator/sync-to-ninja` | Sync lead to Invoice Ninja |
| POST | `/api/webhooks/vapi/` | Vapi.ai webhook |
| POST | `/api/webhooks/messaging/` | Messaging webhook |
| POST | `/api/webhooks/messaging/telegram` | Telegram webhook |
| GET | `/docs` | Swagger API docs |

## Fallback Mode

All commercial services (Invoice Ninja, Cal.com, local LLM) have **graceful fallback modes**. The application works fully offline without any external services:

- **LLM unavailable** → Returns structured mock data with `Unknown` placeholders
- **Invoice Ninja unavailable** → Creates mock client/invoice IDs, logs payloads for later sync
- **Cal.com unavailable** → Returns mock booking URLs with `apex.local` domain

This makes the sandbox fully testable without any paid services.

## Project Structure

```
aiClientSupport/
├── .env.example              # Environment template
├── .gitignore
├── .clinerules               # AI coding rules
├── requirements.txt          # Python dependencies
├── run.sh                    # One-command launcher
├── README.md
├── memory-bank/              # Context persistence
│   ├── goals.md
│   ├── errors.md
│   └── environment.md
└── app/
    ├── __init__.py
    ├── main.py               # FastAPI entry point
    ├── config.py             # Settings from env vars
    ├── database.py           # SQLAlchemy setup
    ├── models.py             # Lead, Invoice, CallLog models
    ├── services/
    │   ├── llm_engine.py     # Local LLM integration
    │   ├── invoice_ninja_client.py  # Invoice Ninja API
    │   └── calendar_service.py      # Cal.com integration
    └── routers/
        ├── simulator.py      # Interactive simulator endpoints
        ├── vapi_webhooks.py  # Vapi.ai webhook handler
        ├── messaging_webhooks.py  # SMS/Telegram webhooks
        └── invoices.py       # Invoice parsing + dashboard stats
```

## License

Private - Apex Home Services