"""
FastAPI app for the production reporting project.

main.py is deliberately thin: it creates exactly one ProductionReportingWorkflow
instance and every route does nothing but call one of its methods. It never
touches a Flow, a Connection, or the database directly.

Start:  uvicorn main:app --reload
Docs:   http://127.0.0.1:8000/docs
"""
from datetime import datetime
from typing import Optional
from models.measure import MeasureIn
from fastapi import FastAPI, HTTPException, Query

from workflows.production_reporting_workflow import ProductionReportingWorkflow

app = FastAPI(
    title="Production Hall Reporting API",
    description="Error rates, tickets, usage history & measure-effect tracking "
                "for production machines (dryers, cooling tunnels, packaging robots, ...).",
    version="0.3.0",
)

workflow = ProductionReportingWorkflow()


@app.get("/")
def root():
    return {"message": "Production Hall Reporting API is running. Docs at /docs"}


@app.get("/machines")
def list_machines():
    return [vars(m) for m in workflow.get_machines()]


@app.get("/machines/{machine_id}/events")
def machine_events(machine_id: int, start: Optional[datetime] = None, end: Optional[datetime] = None):
    events = workflow.get_machine_events(machine_id, start, end)
    if not events:
        raise HTTPException(404, "No events found for this machine/time range")
    return [vars(e) for e in events]


@app.get("/tickets")
def list_tickets(machine_id: Optional[int] = None, limit: int = 50):
    return [vars(t) for t in workflow.get_tickets(machine_id, limit)]


@app.get("/kpi/error-rate")
def kpi_error_rate():
    return [vars(r) for r in workflow.get_error_rate_kpi()]


@app.get("/kpi/availability")
def kpi_availability():
    return [vars(r) for r in workflow.get_availability_kpi()]


@app.get("/kpi/mttr-mtbf")
def kpi_mttr_mtbf():
    return [vars(r) for r in workflow.get_mttr_mtbf_kpi()]


@app.post("/measures")
def create_measure(payload: MeasureIn):
    result = workflow.create_measure(payload.machine_id, payload.description, payload.start_date)
    if result is None:
        raise HTTPException(404, "Machine not found")

    machine_name, measure, effect = result
    return {"measure_id": measure.id, "machine": machine_name, "effect": vars(effect)}


@app.get("/measures")
def list_measures():
    return [
        {"id": measure.id, "machine": machine_name, "description": measure.description,
         "start_date": measure.start_date, "effect": vars(effect)}
        for machine_name, measure, effect in workflow.list_measures()
    ]


@app.get("/tickets/clusters")
def ticket_clusters(n_clusters: int = Query(5, ge=2, le=10)):
    try:
        return [vars(r) for r in workflow.get_ticket_clusters(n_clusters)]
    except ValueError as error:
        raise HTTPException(400, str(error))
