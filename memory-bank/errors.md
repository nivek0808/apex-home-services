# Errors - Apex Home Services

## Known Issues & Resolutions

### [Stats Endpoint Routing Mismatch]
- **Date Encountered:** 2026-07-30
- **Error Description:** Dashboard frontend calls `/api/dashboard/stats` but the FastAPI router mounts it at `/dashboard/stats` (no `/api` prefix)
- **Root Cause:** `invoices.py` router uses `router = APIRouter(tags=["invoices"])` without prefix, but frontend JavaScript assumed `/api/` prefix like other endpoints
- **Resolution:** Updated `index.html` to fetch from `/dashboard/stats` instead of `/api/dashboard/stats`
- **Status:** Fixed

---

*Last updated: 2026-07-30 - Stats endpoint routing fixed*
