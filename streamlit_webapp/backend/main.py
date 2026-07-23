"""
Production Hall Reporting API.

Start (aus dem Ordner `backend/`):
    uvicorn main:application --reload
"""
from __future__ import annotations

from workflows.bootstrap import BuildApiWorkflow

application = BuildApiWorkflow().run()
