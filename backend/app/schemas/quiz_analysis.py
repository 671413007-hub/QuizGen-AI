from typing import List

from pydantic import BaseModel, Field


class QuizAnswerItem(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str
    topic: str
    user_answer: str


class QuizAnalysisRequest(BaseModel):
    questions: List[QuizAnswerItem] = Field(
        min_length=1
    )


class WrongQuestion(BaseModel):
    question_index: int
    question: str
    user_answer: str
    correct_answer: str
    topic: str
    explanation: str


class WeakTopic(BaseModel):
    topic: str
    wrong_count: int
    reason: str
    recommendation: str


class QuizAnalysisResponseData(BaseModel):
    total_questions: int
    correct_count: int
    wrong_count: int
    score_percentage: float

    wrong_questions: List[WrongQuestion]

    weak_topics: List[WeakTopic]

    overall_analysis: str

    study_recommendations: List[str]


class QuizAnalysisResponse(BaseModel):
    success: bool
    message: str
    data: QuizAnalysisResponseData