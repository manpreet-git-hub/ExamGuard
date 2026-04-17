# ── backend/routers/submissions.py — Exam submissions + auto-grading ──────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database.db import get_db
from models.models import Submission, Answer, Question, Test, User, QuestionType
from routers.auth import get_current_user
from utils.test_access import ensure_student_user, ensure_test_available_for_student

router = APIRouter()


class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    selected_options: Optional[List[str]] = None

class SubmissionCreate(BaseModel):
    test_id: int

class SubmitAnswers(BaseModel):
    answers: List[AnswerSubmit]
    time_taken_secs: Optional[int] = None

class SubmissionOut(BaseModel):
    id: int
    test_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    score: float
    max_score: int
    percentage: float
    passed: bool
    integrity_score: float
    risk_level: str
    is_submitted: bool

    class Config:
        from_attributes = True


def grade_answer(question, answer_text, selected_options):
    if question.question_type == QuestionType.mcq:
        correct = question.correct_answer
        selected = selected_options[0] if selected_options else None
        is_correct = selected == correct
        return is_correct, question.marks if is_correct else 0
    elif question.question_type == QuestionType.multiple_correct:
        correct = set(question.correct_answer or [])
        selected = set(selected_options or [])
        is_correct = correct == selected
        return is_correct, question.marks if is_correct else 0
    elif question.question_type in [QuestionType.short_answer, QuestionType.coding]:
        return None, 0
    return False, 0


@router.post("/start", response_model=SubmissionOut, status_code=201)
def start_submission(data: SubmissionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_student_user(current_user)
    existing = db.query(Submission).filter(
        Submission.test_id == data.test_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == False
    ).first()
    if existing:
        return existing
    test = db.query(Test).filter(Test.id == data.test_id).first()
    test = ensure_test_available_for_student(test)
    if len(test.questions) == 0:
        raise HTTPException(status_code=400, detail="This test has no questions yet")
    submission = Submission(test_id=data.test_id, student_id=current_user.id, max_score=test.total_marks)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/active/{test_id}", response_model=SubmissionOut)
def get_active_submission(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(Submission.test_id == test_id, Submission.student_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No submission found")
    return sub


@router.post("/{submission_id}/save-answer")
def save_answer(submission_id: int, answer: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == False
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    existing = db.query(Answer).filter(Answer.submission_id == submission_id, Answer.question_id == answer.question_id).first()
    if existing:
        existing.answer_text = answer.answer_text
        existing.selected_options = answer.selected_options
        existing.answered_at = datetime.utcnow()
    else:
        db.add(Answer(submission_id=submission_id, question_id=answer.question_id, answer_text=answer.answer_text, selected_options=answer.selected_options))
    db.commit()
    return {"status": "saved"}


@router.post("/{submission_id}/submit", response_model=SubmissionOut)
def submit_exam(submission_id: int, data: SubmitAnswers, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == False
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found or already submitted")
    test = sub.test
    total_scored = 0.0
    for ans_data in data.answers:
        q = db.query(Question).filter(Question.id == ans_data.question_id).first()
        if not q or q.test_id != test.id:
            continue
        is_correct, marks = grade_answer(q, ans_data.answer_text, ans_data.selected_options or [])
        existing = db.query(Answer).filter(Answer.submission_id == submission_id, Answer.question_id == ans_data.question_id).first()
        if existing:
            existing.answer_text = ans_data.answer_text
            existing.selected_options = ans_data.selected_options
            existing.is_correct = is_correct
            existing.marks_awarded = marks
        else:
            db.add(Answer(submission_id=submission_id, question_id=ans_data.question_id, answer_text=ans_data.answer_text, selected_options=ans_data.selected_options, is_correct=is_correct, marks_awarded=marks))
        total_scored += marks
    percentage = (total_scored / test.total_marks * 100) if test.total_marks > 0 else 0
    sub.score = total_scored
    sub.percentage = round(percentage, 2)
    sub.passed = total_scored >= test.passing_marks
    sub.submitted_at = datetime.utcnow()
    sub.time_taken_secs = data.time_taken_secs
    sub.is_submitted = True
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/{submission_id}/answers")
def get_submission_answers(submission_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    return [{"question_id": a.question_id, "answer_text": a.answer_text, "selected_options": a.selected_options, "is_correct": a.is_correct, "marks_awarded": a.marks_awarded} for a in sub.answers]


# ── Student-facing routes ──────────────────────────────────────────────────────

@router.get("/student/submissions")
def get_student_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return all submissions for the logged-in student."""
    subs = db.query(Submission).filter(
        Submission.student_id == current_user.id,
        Submission.is_submitted == True
    ).order_by(Submission.submitted_at.desc()).all()

    return [
        {
            "id":              s.id,
            "test_id":         s.test_id,
            "test_title":      s.test.title,
            "score":           s.score,
            "max_score":       s.max_score,
            "percentage":      s.percentage,
            "passed":          s.passed,
            "integrity_score": s.integrity_score,
            "risk_level":      s.risk_level,
            "time_taken_secs": s.time_taken_secs,
            "submitted_at":    s.submitted_at,
            "is_submitted":    s.is_submitted,
        }
        for s in subs
    ]
