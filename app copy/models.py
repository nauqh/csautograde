from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    exam_id = Column(String, ForeignKey('exams.id'))
    answers = Column(JSON)
    submitted_at = Column(DateTime(timezone=True),
                          server_default=func.now(), nullable=False)

    exam = relationship("Exam", back_populates="submissions")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(String, primary_key=True)
    name = Column(String)
    url = Column(String)

    submissions = relationship("Submission", back_populates="exam")
