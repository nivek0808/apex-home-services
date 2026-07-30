#!/usr/bin/env bash
set -euo pipefail

echo "=== Apex Home Services - Sandbox ==="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "[1/3] Installing Python dependencies..."
    pip install -q -r requirements.txt
fi

# Initialize database
echo "[2/3] Initializing database..."
python -c "from app.database import init_db; init_db(); print('  Database ready.')"

# Start server
echo "[3/3] Starting server on http://localhost:8000..."
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload