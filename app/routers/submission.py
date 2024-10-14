from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from .. import models
from ..schemas import Submission, SubmissionResponse
from ..database import get_db

router = APIRouter(
    prefix="/submissions",
    tags=['Submissions']
)


# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def add_submission(data: Submission, db: Session = Depends(get_db)):
#     """Add a new submission to the database.

#     Returns:
#         A message indicating the submission was added.
#     """
#     submission = models.Submission(**data.model_dump())
#     db.add(submission)
#     db.commit()

#     return f"Added submission for {submission.email}"


@router.get("/", response_model=SubmissionResponse)
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
