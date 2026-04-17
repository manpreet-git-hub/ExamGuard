# ── backend/routers/student.py — Student-specific endpoints ────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import Submission, User
from routers.auth import get_current_user

router = APIRouter()


@router.get("/submissions")
def get_my_submissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subs = db.query(Submission).filter(
        Submission.student_id == current_user.id,
        Submission.is_submitted == True
    ).order_by(Submission.submitted_at.desc()).all()

    return [
        {
            "id":              s.id,
            "test_id":         s.test_id,
            "test_title":      s.test.title if s.test else "Unknown Test",
            "score":           s.score or 0,
            "max_score":       s.max_score or 0,
            "percentage":      s.percentage or 0,
            "passed":          s.passed or False,
            "integrity_score": s.integrity_score or 100,
            "risk_level":      s.risk_level or "Low",
            "time_taken_secs": s.time_taken_secs,
            "submitted_at":    s.submitted_at,
            "is_submitted":    s.is_submitted,
        }
        for s in subs
    ]


@router.get("/result/{submission_id}")
def get_my_result(submission_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == True
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Result not found")

    answers = [
        {
            "question_id":      a.question_id,
            "question_text":    a.question.question_text,
            "question_type":    a.question.question_type.value if hasattr(a.question.question_type, 'value') else str(a.question.question_type),
            "answer_text":      a.answer_text,
            "selected_options": a.selected_options,
            "correct_answer":   a.question.correct_answer,
            "is_correct":       a.is_correct,
            "marks_awarded":    a.marks_awarded or 0,
            "max_marks":        a.question.marks,
        }
        for a in sub.answers
    ]

    violations = [
        {
            "id":              v.id,
            "violation_type":  v.violation_type,
            "description":     v.description,
            "timestamp":       v.timestamp,
            "penalty_applied": v.penalty_applied or 0,
        }
        for v in sorted(sub.violations, key=lambda x: x.timestamp)
    ]

    return {
        "submission": {
            "id":              sub.id,
            "test_title":      sub.test.title if sub.test else "Unknown",
            "score":           sub.score or 0,
            "max_score":       sub.max_score or 0,
            "percentage":      sub.percentage or 0,
            "passed":          sub.passed or False,
            "passing_marks":   sub.test.passing_marks if sub.test else 0,
            "integrity_score": sub.integrity_score or 100,
            "risk_level":      sub.risk_level or "Low",
            "time_taken_secs": sub.time_taken_secs,
            "submitted_at":    sub.submitted_at,
        },
        "answers":    answers,
        "violations": violations,
    }
