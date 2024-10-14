from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from csautograde import M12Marker, M11Marker, M21Marker, M31Marker, create_summary
import requests

from sqlalchemy.orm import Session
from .schemas import Submission, SubmissionResponse

# Database
from . import models
from .database import engine, get_db

# Routers
from .routers import submission, exam

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='CS Exam Python Client',
    summary="Client for learner submissions",
    version='0.0.6'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# app.include_router(submission.router)
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


@app.get("/submissions", response_model=SubmissionResponse)
async def get_submission(email: str, exam: str, db: Session = Depends(get_db)):
    """Get a submission by email and exam.

    Returns:
        The submission.
    """
    email_exists = db.query(models.Submission).filter(
        models.Submission.email == email).first()
    if not email_exists:
        raise HTTPException(
            status_code=404, detail=f"Email {email} not found")

    exam_exists = db.query(models.Exam).filter(
        models.Exam.id == exam).first()
    if not exam_exists:
        raise HTTPException(
            status_code=404, detail=f"Exam {exam} not found")

    assignment = db.query(models.Submission).filter(
        models.Submission.email == email,
        models.Submission.exam_id == exam
    ).order_by(models.Submission.submitted_at.desc()).first()

    if assignment is None:
        raise HTTPException(
            status_code=404, detail="No submission found for the provided email and exam.")

    return assignment


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
