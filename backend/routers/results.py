# ── backend/routers/results.py ─────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import Submission, Test, User
from routers.auth import get_current_user, require_teacher

router = APIRouter()


def _monitor_sort_key(submission):
    last_event = submission.submitted_at or submission.started_at
    return (
        0 if not submission.is_submitted else 1,
        -(last_event.timestamp() if last_event else 0),
    )


def _latest_submission_per_student(submissions):
    latest = {}
    for submission in submissions:
        existing = latest.get(submission.student_id)
        if existing is None or _monitor_sort_key(submission) < _monitor_sort_key(existing):
            latest[submission.student_id] = submission
    return list(latest.values())


@router.get("/test/{test_id}")
def get_test_results(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    submissions = db.query(Submission).filter(Submission.test_id == test_id, Submission.is_submitted == True).all()

    results = []
    for s in submissions:
        violation_counts = {}
        for v in s.violations:
            violation_counts[v.violation_type] = violation_counts.get(v.violation_type, 0) + 1
        results.append({
            "submission_id":   s.id,
            "student_id":      s.student_id,
            "student_name":    s.student.full_name,
            "student_email":   s.student.email,
            "score":           s.score or 0,
            "max_score":       s.max_score or test.total_marks,
            "percentage":      s.percentage or 0,
            "passed":          s.passed or False,
            "integrity_score": s.integrity_score or 100,
            "risk_level":      s.risk_level or "Low",
            "violations_count": len(s.violations),
            "violation_types": violation_counts,
            "time_taken_secs": s.time_taken_secs,
            "submitted_at":    s.submitted_at,
        })

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    avg_score = sum(r["percentage"] for r in results) / total if total else 0
    avg_integrity = sum(r["integrity_score"] for r in results) / total if total else 100
    high_risk = sum(1 for r in results if r["risk_level"] == "High")

    return {
        "test": {"id": test.id, "title": test.title, "total_marks": test.total_marks, "passing_marks": test.passing_marks},
        "results": results,
        "stats": {"total": total, "passed": passed, "avg_score": avg_score, "avg_integrity": avg_integrity, "high_risk": high_risk},
    }


@router.get("/test/{test_id}/monitor")
def get_test_monitor(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    submissions = db.query(Submission).filter(Submission.test_id == test_id).all()
    students = []

    for submission in sorted(_latest_submission_per_student(submissions), key=_monitor_sort_key):
        latest_violation = max(submission.violations, key=lambda item: item.timestamp, default=None)
        students.append({
            "submission_id": submission.id,
            "student_id": submission.student_id,
            "student_name": submission.student.full_name,
            "student_email": submission.student.email,
            "integrity_score": submission.integrity_score or 100,
            "risk_level": submission.risk_level or "Low",
            "violations_count": len(submission.violations),
            "last_violation": latest_violation.violation_type if latest_violation else None,
            "last_violation_at": latest_violation.timestamp if latest_violation else None,
            "percentage": submission.percentage if submission.is_submitted else None,
            "time_taken_secs": submission.time_taken_secs,
            "started_at": submission.started_at,
            "submitted_at": submission.submitted_at,
            "is_submitted": submission.is_submitted,
            "is_active": not submission.is_submitted,
        })

    total = len(students)
    avg_integrity = sum(item["integrity_score"] for item in students) / total if total else 100
    high_risk = sum(1 for item in students if item["risk_level"] == "High")
    active = sum(1 for item in students if item["is_active"])

    return {
        "test": {
            "id": test.id,
            "title": test.title,
            "access_code": test.access_code,
        },
        "students": students,
        "stats": {
            "total": total,
            "active": active,
            "submitted": total - active,
            "avg_integrity": avg_integrity,
            "high_risk": high_risk,
        },
    }


@router.get("/submission/{submission_id}/detail")
def get_submission_detail(submission_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    if sub.test.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    violations = [
        {
            "id": v.id, "violation_type": v.violation_type,
            "confidence_score": v.confidence_score or 1.0,
            "description": v.description, "evidence_path": v.evidence_path,
            "timestamp": v.timestamp, "penalty_applied": v.penalty_applied or 0,
        }
        for v in sorted(sub.violations, key=lambda x: x.timestamp)
    ]

    answers = [
        {
            "question_id": a.question_id, "question_text": a.question.question_text,
            "question_type": a.question.question_type.value if hasattr(a.question.question_type, 'value') else a.question.question_type,
            "answer_text": a.answer_text, "selected_options": a.selected_options,
            "correct_answer": a.question.correct_answer,
            "is_correct": a.is_correct, "marks_awarded": a.marks_awarded or 0,
            "max_marks": a.question.marks,
        }
        for a in sub.answers
    ]

    return {
        "submission": {
            "id": sub.id, "student_name": sub.student.full_name, "student_email": sub.student.email,
            "score": sub.score or 0, "max_score": sub.max_score or 0,
            "percentage": sub.percentage or 0, "passed": sub.passed or False,
            "integrity_score": sub.integrity_score or 100, "risk_level": sub.risk_level or "Low",
            "started_at": sub.started_at, "submitted_at": sub.submitted_at,
            "time_taken_secs": sub.time_taken_secs,
        },
        "violations": violations,
        "answers": answers,
    }
