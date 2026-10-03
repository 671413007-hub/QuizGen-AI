from typing import List, Literal

from pydantic import BaseModel, Field


class Question(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str
    topic: str


class QuizGenerationRequest(BaseModel):
    content: str = Field(
        min_length=1,
        description="เนื้อหาที่ใช้สร้างข้อสอบ"
    )

    question_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="จำนวนข้อ"
    )

    question_type: Literal[
        "multiple-choice",
        "true-false",
        "short-answer"
    ] = "multiple-choice"

    difficulty: Literal[
        "easy",
        "medium",
        "hard"
    ] = "medium"


class QuizGenerationResponse(BaseModel):
    success: bool
    message: str
    questions: List[Question]