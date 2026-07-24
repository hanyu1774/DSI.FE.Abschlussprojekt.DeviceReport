from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import kpis, measures, reference, tickets


class BuildApiWorkflow:
    def run(self) -> FastAPI:
        application = FastAPI(
            title="FastAPI App für Machine Report",
            description=(
                "FastAPI für Maschinen, Events, Incidents & Service Requests "
                "der Produktionshalle."
            )
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

        @application.get("/", tags=["Status"])
        def root() -> dict[str, str]:
            return {"status": "ok", "service": "production-hall-reporting-api"}

        return application
