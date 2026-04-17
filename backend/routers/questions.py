# ── backend/routers/questions.py ───────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any

from database.db import get_db
from models.models import Question, Test, QuestionType, User
from routers.auth import get_current_user, require_teacher

router = APIRouter()


def prepare_question_payload(*, question_type, options, correct_answer, marks, order_index):
    if marks is not None and marks <= 0:
        raise HTTPException(status_code=400, detail="Marks must be greater than 0")
    if order_index is not None and order_index < 0:
        raise HTTPException(status_code=400, detail="Order index cannot be negative")

    if question_type in [QuestionType.mcq, QuestionType.multiple_correct]:
        clean_options = [opt.strip() for opt in (options or []) if opt and opt.strip()]
        if len(clean_options) < 2:
            raise HTTPException(
                status_code=400,
                detail="Choice questions must include at least two options",
            )

        if question_type == QuestionType.mcq:
            if not isinstance(correct_answer, str) or not correct_answer.strip():
                raise HTTPException(
                    status_code=400,
                    detail="MCQ questions require one correct answer",
                )
            correct_answer = correct_answer.strip()
            if correct_answer not in clean_options:
                raise HTTPException(
                    status_code=400,
                    detail="Correct answer must match one of the options",
                )
        else:
            if not isinstance(correct_answer, list) or len(correct_answer) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Multiple-correct questions require at least one correct option",
                )
            clean_correct = []
            for item in correct_answer:
                if isinstance(item, str):
                    value = item.strip()
                    if value and value in clean_options and value not in clean_correct:
                        clean_correct.append(value)
            if not clean_correct:
                raise HTTPException(
                    status_code=400,
                    detail="Correct answers must match the provided options",
                )
            correct_answer = clean_correct

        return {
            "options": clean_options,
            "correct_answer": correct_answer,
        }

    return {
        "options": None,
        "correct_answer": correct_answer.strip() if isinstance(correct_answer, str) else correct_answer,
    }


class QuestionCreate(BaseModel):
    test_id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    marks: int = 1
    order_index: int = 0
    explanation: Optional[str] = None

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    marks: Optional[int] = None
    order_index: Optional[int] = None
    explanation: Optional[str] = None

class QuestionOut(BaseModel):
    id: int
    test_id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]]
    correct_answer: Optional[Any]
    marks: int
    order_index: int
    explanation: Optional[str]

    class Config:
        from_attributes = True

class QuestionStudent(BaseModel):
    id: int
    test_id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]]
    marks: int
    order_index: int

    class Config:
        from_attributes = True


@router.post("/", response_model=QuestionOut, status_code=201)
def create_question(q: QuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == q.test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    # Auto-set order_index to end of list
    count = len(test.questions)
    payload = prepare_question_payload(
        question_type=q.question_type,
        options=q.options,
        correct_answer=q.correct_answer,
        marks=q.marks,
        order_index=q.order_index,
    )
    question = Question(
        **q.dict(exclude={"options", "correct_answer"}),
        options=payload["options"],
        correct_answer=payload["correct_answer"],
    )
    if q.order_index == 0:
        question.order_index = count
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/test/{test_id}", response_model=List[QuestionOut])
def get_test_questions(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    test = db.query(Test).filter(Test.id == test_id, Test.creator_id == current_user.id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return sorted(test.questions, key=lambda q: q.order_index)


@router.get("/student/test/{test_id}", response_model=List[QuestionStudent])
def get_questions_for_student(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return questions without correct answers — for students taking the exam."""
    test = db.query(Test).filter(Test.id == test_id, Test.is_active == True).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found or inactive")
    return sorted(test.questions, key=lambda q: q.order_index)


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, q: QuestionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.test.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updates = q.dict(exclude_none=True)
    question_type = updates.get("question_type", question.question_type)
    prepared = prepare_question_payload(
        question_type=question_type,
        options=updates.get("options", question.options),
        correct_answer=updates.get("correct_answer", question.correct_answer),
        marks=updates.get("marks", question.marks),
        order_index=updates.get("order_index", question.order_index),
    )
    updates["options"] = prepared["options"]
    updates["correct_answer"] = prepared["correct_answer"]
    for k, v in updates.items():
        setattr(question, k, v)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.test.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(question)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/reorder")
def reorder_questions(orders: List[dict], db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    for item in orders:
        q = db.query(Question).filter(Question.id == item["id"]).first()
        if q and q.test.creator_id == current_user.id:
            q.order_index = item["order_index"]
    db.commit()
    return {"detail": "Reordered"}
