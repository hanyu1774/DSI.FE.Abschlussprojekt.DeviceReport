"""
Einstiegspunkt für diese FastAPI App.

Start (aus dem Ordner `backend/`):
    uvicorn main:application --reload
"""
from __future__ import annotations

from workflows.build_api_workflow import BuildApiWorkflow

application = BuildApiWorkflow().run()



