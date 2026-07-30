"""Apex Home Services - FastAPI Application Entry Point."""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import simulator, vapi_webhooks, messaging_webhooks, invoices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from .env file (project root)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    init_db()
    logger.info("Database tables created. Apex Home Services starting.")
    yield
    logger.info("Apex Home Services shutting down.")


app = FastAPI(
    title="Apex Home Services",
    description="Full-Stack Automation & System Mirror Sandbox for SMB home services",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simulator.router)
app.include_router(vapi_webhooks.router)
app.include_router(messaging_webhooks.router)
app.include_router(invoices.router)


@app.get("/")
async def root():
    """Serve the dashboard HTML."""
    return FileResponse("app/templates/index.html")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Apex Home Services"}