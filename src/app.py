"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from storage import Storage

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

storage = Storage(current_dir / "data" / "school.db")


@app.on_event("startup")
def on_startup() -> None:
    storage.initialize()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return storage.get_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    try:
        created = storage.signup_for_activity(activity_name=activity_name, email=email)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    if not created:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    try:
        removed = storage.unregister_from_activity(activity_name=activity_name, email=email)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    if not removed:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": f"Unregistered {email} from {activity_name}"}
