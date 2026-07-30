# Apex Home Services - Project Status

**Last Updated:** 2026-07-30 19:30 UTC
**Main App URL:** http://127.0.0.1:8999/
**Project Path:** `/root/workspace/aiClientSupport/`

---

## Current System Status

### All Services

| Service | Status | URL | Credentials/Notes |
|---------|--------|-----|-------------------|
| **Apex Main App** | ✅ Healthy | http://localhost:8999/ | FastAPI/Python |
| **AI Assistant** | ✅ Healthy | 127.0.0.1:8999/dashboard | Google AI Studio - gemini-3.5-flash-lite |
| **Calendar (Cal.com)** | ✅ Healthy | http://localhost:3000/ | Needs initial user setup (redirects to login) |
| **n8n Automation** | ✅ Healthy | http://localhost:5678/ | Default: admin / apex_n8n_2026 |
| **Invoice Ninja** | ✅ Healthy | http://localhost:8003/ | **admin@example.com / password** |

### App Database Stats
- **Leads:** 5 total, 5 active, 1 emergency
- **Calls:** 5 total, 1 emergency call
- **Invoices:** 1 total ($0.00 - test only)

---

## Docker Compose Services

```
apex-invoice-ninja  - Invoice Ninja (PHP-FPM + nginx, CUSTOM IMAGE) - WORKING
apex-mysql          - MySQL 8.0 for Invoice Ninja - WORKING
apex-n8n            - n8n workflow automation - WORKING
apex-cal-com        - Cal.com scheduling - WORKING (needs setup)
apex-postgres       - PostgreSQL for Cal.com - WORKING
```

---

## Invoice Ninja - Fix Details (2026-07-30)

### Problem Solved
The official `invoiceninja/invoiceninja:latest` Docker image only includes **PHP-FPM** — no web server at all. This is why the container was "running" but HTTP requests returned nothing (no server listening on port 80).

### Fix Applied
Built a **custom Docker image** (`apex-invoice-ninja:custom`) that adds:
- **Nginx** web server configured to proxy to PHP-FPM on port 9000
- **Laravel routing** (try_files $uri $uri/ /index.php?$query_string)
- **Security** (deny access to hidden files, .git, static asset caching)
- **Supervisor config** includes nginx so it auto-starts and survives restarts
- Proper file permissions for the non-root `invoiceninja` user (uid 1500)

### Files Created
| File | Purpose |
|------|---------|
| `/root/workspace/aiClientSupport/Dockerfile` | Builds custom image with nginx |
| `/root/workspace/aiClientSupport/nginx-http.conf` | Nginx server block for Laravel |
| `/root/workspace/aiClientSupport/supervisord.conf` | Supervisor config with nginx + php-fpm + scheduler + queue |
| `/root/workspace/aiClientSupport/docker-compose.yml` | Updated to use custom image, map port 8003→80 |

### Important Notes
- **APP_KEY** must be set in environment variables (Laravel requirement)
- Default admin: `admin@example.com` / `password` (password reset applied)
- Docker compose uses `apex-invoice-ninja:custom` image (built from Dockerfile)
- Port mapping: `8003:80` (nginx listens on port 80 inside container)

---

## Main App Fix Details (2026-07-30)

### Problem Solved
Port 8999 (Apex Main App) was returning HTTP 500 because the uvicorn process was running from the **old path** `/root/aiClientSupport/` which no longer exists after the directory migration to `/root/workspace/aiClientSupport/`.

Additionally, the virtual environment's compiled bytecode (.pyc files) was corrupted from the path change, causing `ValueError: bad marshal data (unknown type code)` on every import.

### Fix Applied
1. Rebuilt the virtual environment from scratch: `rm -rf .venv && python3 -m venv .venv && pip install -r requirements.txt`
2. Restarted uvicorn from the correct path: `/root/workspace/aiClientSupport`
3. App now imports successfully and serves HTTP 200

### Important Notes
- Virtual environment corrupted when project moved — always rebuild `.venv` after path changes
- Uvicorn command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8999`
- Start via: `cd /root/workspace/aiClientSupport && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8999`

---

## Data Storage Locations

| Service | Database | Docker Volume | Purpose |
|---------|----------|---------------|---------|
| **Cal.com** | PostgreSQL (`apex-postgres`) | `postgres_data` | Appointments, bookings, users, CRM |
| **Invoice Ninja** | MySQL (`apex-mysql`) | `mysql_data` | Invoices, billing, clients, vendors |
| **Apex Main App** | SQLite (local) | N/A (ephemeral) | Leads, call logs, cached invoices |

---

## Architecture

```
Port 8999 → Apex Main App (FastAPI/Python)
  ├── /health → System health check
  ├── /dashboard/stats → Integration status + database stats
  ├── /api/leads → Lead management
  ├── /api/invoices/parse → Invoice parsing (Google AI)
  └── /api/voice → Voice call simulation

Port 8003 → Invoice Ninja (PHP/Laravel + nginx) - WORKING
Port 5678 → n8n (Node.js) - WORKING
Port 3000 → Cal.com (Next.js) - WORKING (needs setup)

Databases:
  MySQL → apex-mysql (volume: mysql_data)
  PostgreSQL → apex-postgres (volume: postgres_data)
  SQLite → Local to Apex container
```

---

## Known Issues

### 1. Cal.com - Initial Setup Required
- Container is running and responsive
- Redirects to `/auth/login` (expected for fresh install)
- Needs: create admin user, configure email, connect calendars
- URL: http://localhost:3000/

### 2. n8n - Basic Auth Configured
- Running on port 5678
- Default credentials: admin / apex_n8n_2026
- Needs: set up workflows to connect services

---

## Configuration Files

| File | Purpose |
|------|---------|
| `/root/workspace/aiClientSupport/docker-compose.yml` | Docker orchestration |
| `/root/workspace/aiClientSupport/.env` | API keys and environment variables |
| `/root/workspace/aiClientSupport/app/config.py` | Python app configuration |
| `/root/workspace/aiClientSupport/app/services/llm_engine.py` | Google AI integration |
| `/root/workspace/aiClientSupport/app/routers/invoices.py` | Dashboard stats + invoice parsing |
| `/root/workspace/aiClientSupport/Dockerfile` | Custom Invoice Ninja image build |
| `/root/workspace/aiClientSupport/nginx-http.conf` | Nginx config for Invoice Ninja |
| `/root/workspace/aiClientSupport/supervisord.conf` | Supervisor config for Invoice Ninja |

---

## Next Steps (When You Return)

1. **Setup Cal.com** - Create admin account, configure email/calendar
2. **Setup n8n** - Create workflows to connect services
3. **Connect Invoice Ninja to Apex App** - Make `/api/invoices/parse` actually push invoices
4. **Test end-to-end** - Parse invoice → create client in Ninja → create invoice

---

## Security Notes

- All credentials stored in `/root/workspace/aiClientSupport/.env`
- Docker volumes `mysql_data` and `postgres_data` persist all data
- SQLite database is local to the Apex container (not in volumes)
- Google AI API key configured in `.env` as `GOOGLE_AI_API_KEY`
- Invoice Ninja admin: `admin@example.com` / `password`
- n8n basic auth: admin / apex_n8n_2026

---

## Troubleshooting Quick Reference

### Venv corrupted (bad marshal data)?
```bash
cd /root/workspace/aiClientSupport
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Restart main app on 8999?
```bash
cd /root/workspace/aiClientSupport
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8999
```

### Restart Invoice Ninja?
```bash
cd /root/workspace/aiClientSupport
docker compose down invoice-ninja
docker compose up -d invoice-ninja
```

### Invoice Ninja not responding?
Check: nginx is running inside container, APP_KEY is set, port mapping is 8003:80
