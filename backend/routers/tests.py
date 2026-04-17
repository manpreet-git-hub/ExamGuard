# ── backend/routers/tests.py — Test CRUD ──────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random, string

from database.db import get_db
from models.models import Test, User, UserRole
from routers.auth import get_current_user, require_teacher
from utils.test_access import ensure_test_available_for_student, validate_test_settings

router = APIRouter()


def gen_access_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    duration_mins: int
    total_marks: int
    passing_marks: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_mins: Optional[int] = None
    total_marks: Optional[int] = None
    passing_marks: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None

class TestOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    access_code: str
    duration_mins: int
    total_marks: int
    passing_marks: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_active: bool
    creator_id: int
    created_at: datetime
    question_count: Optional[int] = 0
    submission_count: Optional[int] = 0

    class Config:
        from_attributes = True


@router.post("/", response_model=TestOut, status_code=201)
def create_test(test_data: TestCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    validate_test_settings(
        duration_mins=test_data.duration_mins,
        total_marks=test_data.total_marks,
        passing_marks=test_data.passing_marks,
        start_time=test_data.start_time,
        end_time=test_data.end_time,
    )
    code = gen_access_code()
    while db.query(Test).filter(Test.access_code == code).first():
        code = gen_access_code()
    test = Test(**test_data.dict(), access_code=code, creator_id=current_user.id)
    db.add(test)
    db.commit()
    db.refresh(test)
    out = TestOut.from_orm(test)
    out.question_count = 0
    out.submission_count = 0
    return out


@router.get("/", response_model=List[TestOut])
def list_tests(db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    tests = db.query(Test).filter(Test.creator_id == current_user.id).order_by(Test.created_at.desc()).all()
    result = []
    for t in tests:
        out = TestOut.from_orm(t)
        out.question_count = len(t.questions)
        out.submission_count = len(t.submissions)
        result.append(out)
    return result


# IMPORTANT: /code/{access_code} must come BEFORE /{test_id}
# otherwise FastAPI tries to cast "code" as an integer and fails
@router.get("/code/{access_code}")
def get_test_by_code(access_code: str, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.access_code == access_code.upper()).first()
    test = ensure_test_available_for_student(test)
    return {
        "id":             test.id,
        "title":          test.title,
        "description":    test.description,
        "duration_mins":  test.duration_mins,
        "total_marks":    test.total_marks,
        "passing_marks":  test.passing_marks,
        "start_time":     test.start_time,
        "end_time":       test.end_time,
        "question_count": len(test.questions),
        "access_code":    test.access_code,
    }


@router.get("/{test_id}", response_model=TestOut)
def get_test(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if current_user.role == UserRole.student:
        ensure_test_available_for_student(test)
    out = TestOut.from_orm(test)
    out.question_count = len(test.questions)
    out.submission_count = len(test.submissions)
    return out


@router.put("/{test_id}", response_model=TestOut)
def update_test(test_id: int, test_data: TestUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    updates = test_data.dict(exclude_none=True)
    validate_test_settings(
        duration_mins=updates.get("duration_mins", test.duration_mins),
        total_marks=updates.get("total_marks", test.total_marks),
        passing_marks=updates.get("passing_marks", test.passing_marks),
        start_time=updates.get("start_time", test.start_time),
        end_time=updates.get("end_time", test.end_time),
    )
    for k, v in updates.items():
        setattr(test, k, v)
    db.commit()
    db.refresh(test)
    out = TestOut.from_orm(test)
    out.question_count = len(test.questions)
    out.submission_count = len(test.submissions)
    return out


@router.delete("/{test_id}")
def delete_test(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    db.delete(test)
    db.commit()
    return {"detail": "Test deleted"}
