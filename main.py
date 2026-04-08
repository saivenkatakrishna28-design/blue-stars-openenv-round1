from typing import Optional
from fastapi import FastAPI, Query
from app.env import SupportTriageEnv
from app.models import Action, StepResult, ResetResponse, State, HealthResponse
from app.tasks import list_task_ids

app = FastAPI(title="Blue Stars Support Triage OpenEnv", version="2.0.0")
env = SupportTriageEnv()


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(status="ok", service="blue-stars-support-triage-openenv", version="2.0.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="blue-stars-support-triage-openenv", version="2.0.0")


@app.get("/tasks")
def tasks():
    return {"tasks": list_task_ids(), "count": len(list_task_ids())}


@app.post("/reset", response_model=ResetResponse)
def reset(task_id: Optional[str] = Query(default=None)) -> ResetResponse:
    return env.reset(task_id=task_id)


@app.get("/state", response_model=State)
def state() -> State:
    return env.state()


@app.post("/step", response_model=StepResult)
def step(action: Action) -> StepResult:
    return env.step(action)
