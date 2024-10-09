from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .schemas import Exam, Submission, SubmissionResponse
from csautograde import M12Marker, M11Marker, M21Marker, M31Marker, create_summary
import requests

# Database
from . import models
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='CS Exam Python Client',
    summary="Client for learner submissions",
    version='0.0.2'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def root():
    return {"message": "Root endpoint"}


@app.post("/submission", status_code=status.HTTP_201_CREATED)
async def add_submission(data: Submission, db: Session = Depends(get_db)):
    submission = models.Submission(**data.model_dump())
    db.add(submission)
    db.commit()

    return f"Added submission for {submission.email}"


@app.get("/submission", response_model=SubmissionResponse)
async def get_assignment(email: str, exam: str, db: Session = Depends(get_db)):
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


@app.post("/exam", status_code=status.HTTP_201_CREATED)
async def add_assignment(data: Exam, db: Session = Depends(get_db)):
    exam = models.Exam(**data.model_dump())
    db.add(exam)
    db.commit()

    return f"Added new assignment: {exam.name}"


@app.get("/exam/{id}", response_model=Exam)
async def get_exam(id: str, db: Session = Depends(get_db)):
    exam = db.query(models.Exam).filter(models.Exam.id == id).first()
    return exam


MARKER_CLASSES = {
    "M11": M11Marker,
    "M12": M12Marker,
    "M21": M21Marker,
    "M31": M31Marker
}


@app.get("/autograde")
def test_endpoint(email: str, exam: str):
    response = requests.get(
        f"https://cspyclient.up.railway.app/submission?email={email}&exam={exam}")
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
    return create_summary(marker.exam_name, marker.summary, marker.QUESTION_SCORES)
