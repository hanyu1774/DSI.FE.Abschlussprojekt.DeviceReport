"""
Production Hall Reporting API.

Datenfluss: Streamlit (Frontend) -> FastAPI (dieses Projekt) -> SQLite.

Start (aus dem Ordner `backend/`):
    uvicorn main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import kpis, measures, reference, tickets

app = FastAPI(
    title="Production Hall Reporting API",
    description=(
        "Reporting-API fuer Maschinen, Events, Incidents & Service Requests "
        "der Produktionshalle."
    ),
    version="2.0.0",
)

# Fuer den lokalen Betrieb (Streamlit auf einem anderen Port) offen konfiguriert.
# Fuer ein Deployment auf allow_origins mit der/den konkreten Frontend-URL(s) einschraenken.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reference.router)
app.include_router(kpis.router)
app.include_router(tickets.router)
app.include_router(measures.router)


@app.get("/", tags=["Status"])
def root() -> dict:
    return {"status": "ok", "service": "production-hall-reporting-api"}
