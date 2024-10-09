from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from csautograde import M12Marker, M11Marker, M21Marker, M31Marker, create_summary
import requests


MARKER_CLASSES = {
    "M11": M11Marker,
    "M12": M12Marker,
    "M21": M21Marker,
    "M31": M31Marker
}

app = FastAPI(
    title='Autograding API',
    summary="Client for autograding learner submissions",
    version='0.0.1'
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
