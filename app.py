import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from graph.travel_graph import run_travel_planner

app = FastAPI(title="AI Travel Planner", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


class TravelRequest(BaseModel):
    user_query: str = Field(min_length=5)


class TravelResponse(BaseModel):
    itinerary: str
    destination: str | None = None
    duration_days: int | None = None
    budget: float | None = None
    currency: str | None = None
    critic_decision: str | None = None
    critic_feedback: str | None = None
    replan_attempts: int = 0


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    html = (open("templates/index.html", encoding="utf-8").read())
    return HTMLResponse(html)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/plan", response_model=TravelResponse)
async def create_plan(payload: TravelRequest):
    result = run_travel_planner(payload.user_query)
    return TravelResponse(
        itinerary=result.get("itinerary", ""),
        destination=result.get("destination"),
        duration_days=result.get("duration_days"),
        budget=result.get("budget"),
        currency=result.get("currency"),
        critic_decision=result.get("critic_decision"),
        critic_feedback=result.get("critic_feedback"),
        replan_attempts=result.get("replan_attempts", 0),
    )
