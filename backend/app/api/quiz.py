from fastapi import APIRouter

from app.schemas.quiz import (
    QuizGenerationRequest,
    QuizGenerationResponse,
)

from app.services.quiz_service import QuizService


router = APIRouter(
    prefix="/api/quiz",
    tags=["Quiz"]
)

service = QuizService()


@router.post(
    "/generate",
    response_model=QuizGenerationResponse
)
def generate_quiz(
    request: QuizGenerationRequest
):
    return service.generate_quiz(request)