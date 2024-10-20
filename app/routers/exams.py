from fastapi import status, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..schemas import Exam
from ..database import get_db

from typing import List


router = APIRouter(
    prefix="/exams",
    tags=['Exams']
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_exam(data: Exam, db: Session = Depends(get_db)):
    """
    Add a new exam to the database.

    Returns:
        str: The success message.
    """
    exam = models.Exam(**data.model_dump())
    db.add(exam)
    db.commit()

    return f"Added new assignment: {exam.name}"


@router.get("/", response_model=List[Exam])
async def get_all_exams(db: Session = Depends(get_db)):
    """
    Retrieves all exams from the database.

    Returns:
        List[Exam]: The list of all exams.
    """
    exams = db.query(models.Exam).all()
    return exams


@router.get("/{id}", response_model=Exam)
async def get_exam(id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single exam from the database by its id.

    Returns:
        Exam: The exam if found.
    """
    exam = db.query(models.Exam).filter(models.Exam.id == id).first()
    if not exam:
        raise HTTPException(
            status_code=404, detail=f"Exam {id} not found")
    return exam
