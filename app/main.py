from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from csautograde import M12Marker, M11Marker, M21Marker, M31Marker, create_summary
import requests

# Database
from . import models
from sqlalchemy.orm import Session
from .database import engine, get_db

from .schemas import Submission

# Routers
from .routers import submission, exam

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='CS Exam Python Client',
    summary="Client for learner submissions",
    version='0.0.4'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(submission.router)
app.include_router(exam.router)


@app.get("/")
def root():
    return {"message": "Root endpoint"}


MARKER_CLASSES = {
    "M11": M11Marker,
    "M12": M12Marker,
    "M21": M21Marker,
    "M31": M31Marker
}


@app.post("/submissions", status_code=status.HTTP_201_CREATED)
async def add_submission(data: Submission, db: Session = Depends(get_db)):
    """Add a new submission to the database.

    Returns:
        A message indicating the submission was added.
    """
    submission = models.Submission(**data.model_dump())
    db.add(submission)
    db.commit()

    return f"Added submission for {submission.email}"


@app.get("/autograde")
def get_autograde(email: str, exam: str):
    response = requests.get(
        f"https://cspyexamclient.up.railway.app/submissions?email={email}&exam={exam}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json()['detail']
        )
    submission = response.json()['answers']
    s = [question['answer'] for question in submission]

    MarkerClass = MARKER_CLASSES.get(exam.upper())
    if MarkerClass is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exam type: {exam}"
        )

    marker = MarkerClass()
    marker.mark_submission(s)
    return {
        'submission': s,
        'summary': create_summary(marker.exam_name, marker.summary, marker.QUESTION_SCORES)
    }
