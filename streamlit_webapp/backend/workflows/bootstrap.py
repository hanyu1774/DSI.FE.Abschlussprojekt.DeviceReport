from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import kpis, measures, reference, tickets


class BuildApiWorkflow:
    """The only Workflow main.py is allowed to call, per Plan #3. Builds and
    returns the fully configured FastAPI app - creation, CORS, router
    registration, and the health-check route all happen here so main.py
    doesn't have to contain anything beyond the one call to run()."""

    def run(self) -> FastAPI:
        application = FastAPI(
            title="Production Hall Reporting API",
            description=(
                "Reporting-API fuer Maschinen, Events, Incidents & Service Requests "
                "der Produktionshalle."
            ),
            version="2.0.0",
        )

        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        application.include_router(reference.router)
        application.include_router(kpis.router)
        application.include_router(tickets.router)
        application.include_router(measures.router)

        # Trivial, static response - no Flow behind it on purpose (see Issue 5
        # in the restructuring plan: not worth the ceremony for a hardcoded dict).
        @application.get("/", tags=["Status"])
        def root() -> dict[str, str]:
            return {"status": "ok", "service": "production-hall-reporting-api"}

        return application
