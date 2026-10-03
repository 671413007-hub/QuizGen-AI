from typing import List, Literal

from pydantic import BaseModel, Field

from app.schemas.quiz import Question


class RemedialQuizRequest(BaseModel):
    original_content: str = Field(
        min_length=1,
        description="เนื้อหาบทเรียนต้นฉบับ"
    )

    weak_topics: List[str] = Field(
        min_length=1,
        description="หัวข้อที่ผู้เรียนยังมีจุดอ่อน"
    )

    question_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="จำนวนข้อสอบแก้จุดอ่อน"
    )

    difficulty: Literal[
        "easy",
        "medium",
        "hard"
    ] = "medium"


class RemedialQuizResponse(BaseModel):
    success: bool
    message: str
    weak_topics: List[str]
    questions: List[Question]