from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from csautograde import M12Marker, M11Marker, M21Marker, M31Marker, create_summary
from datetime import datetime
from pytz import timezone

from sqlalchemy.orm import Session
from .schemas import Submission, SubmissionResponse, SubmissionHistory

# Database
from . import models
from .database import engine, get_db

# Routers
from .routers import exams

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='CS Exam Python Client',
    summary="Client for learner submissions",
    version='0.0.10'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(exams.router)


@app.get("/")
def root():
    return {"message": "Root endpoint"}


MARKER_CLASSES = {
    "M11": M11Marker,
    "M12": M12Marker,
    "M21": M21Marker,
    "M31": M31Marker
}


def validate_email(email: str, db: Session):
    """Validate email exists in database."""
    email_exists = db.query(models.Submission).filter(
        models.Submission.email == email).first()
    if not email_exists:
        raise HTTPException(
            status_code=404, detail=f"Email {email} not found")


def validate_exam(exam: str, db: Session):
    """Validate exam exists in database."""
    exam_exists = db.query(models.Exam).filter(
        models.Exam.id == exam).first()
    if not exam_exists:
        raise HTTPException(
            status_code=404, detail=f"Exam {exam} not found")


@app.get("/submissions/{exam}/{email}", response_model=SubmissionResponse)
async def get_submission(exam: str, email: str, db: Session = Depends(get_db)):
    """Get a submission by email and exam.

    Returns:
        The submission.
    """
    validate_email(email, db)
    validate_exam(exam, db)

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
    # Generate marking summary
    s = [question['answer'] for question in data.answers]

    MarkerClass = MARKER_CLASSES.get(data.exam_id.upper())
    if MarkerClass is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exam type: {exams}"
        )

    marker = MarkerClass()
    marker.mark_submission(s)

    summary, final_score = create_summary(
        marker.exam_name, marker.summary, marker.QUESTION_SCORES)

    # Save to database
    submission = models.Submission(**data.model_dump())
    submission.summary = summary
    submission.score = final_score

    db.add(submission)
    db.commit()

    return f"Added submission for {submission.email}"


@app.put("/submissions/{exam}/{email}", response_model=SubmissionResponse)
async def update_submission(email: str, exam: str, new_score: int, db: Session = Depends(get_db)):
    """Update the score of a submission

    Returns:
        The updated submission
    """
    validate_email(email, db)
    validate_exam(exam, db)

    submission = db.query(models.Submission).filter(
        models.Submission.email == email,
        models.Submission.exam_id == exam
    ).order_by(models.Submission.submitted_at.desc()).first()

    submission.score = new_score
    db.commit()

    return submission


@app.get("/history/{email}", response_model=list[SubmissionHistory])
async def get_submission_history(email: str, db: Session = Depends(get_db)):
    """
    Get submission history for a learner by email.
    """
    validate_email(email, db)

    # Query all submissions by the given email, ordered by the submission date
    submissions = db.query(models.Submission).filter(
        models.Submission.email == email
    ).order_by(models.Submission.submitted_at.asc()).all()

    if not submissions:
        raise HTTPException(
            status_code=404, detail="No submissions found for the provided email.")

    # Prepare and return the submission history
    submission_history = [
        {
            "submitted_at": submission.submitted_at.astimezone(timezone("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S"),
            "exam": submission.exam.name,
            "score": submission.score
        }
        for submission in submissions
    ]

    return submission_history


# @app.get("/autograde")
# def get_autograde(email: str, exam: str):
#     response = requests.get(
#         f"https://cspyexamclient.up.railway.app/submissions?email={email}&exam={exam}")

#     if response.status_code != 200:
#         raise HTTPException(
#             status_code=response.status_code,
#             detail=response.json()['detail']
#         )
#     submission = response.json()['answers']
#     s = [question['answer'] for question in submission]

#     MarkerClass = MARKER_CLASSES.get(exam.upper())
#     if MarkerClass is None:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid exam type: {exam}"
#         )

#     marker = MarkerClass()
#     marker.mark_submission(s)

#     summary, final_score = create_summary(
#         marker.exam_name, marker.summary, marker.QUESTION_SCORES)
#     return {
#         'submission': s,
#         'summary': summary,
#         'final_score': final_score
#     }
