from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from datetime import datetime


class Submission(BaseModel):
    email: str
    answers: list
    exam_id: str


class SubmissionResponse(BaseModel):
    email: str
    answers: list
    exam_id: str
    submitted_at: Optional[datetime]


class Exam(BaseModel):
    id: str
    name: str
    url: str
