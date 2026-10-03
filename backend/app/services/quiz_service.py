from app.schemas.quiz import (
    QuizGenerationRequest,
    QuizGenerationResponse,
)

from app.services.ai_service import AIServiceFactory


class QuizService:

    def __init__(self):
        self.ai_service = AIServiceFactory.get_service()

    def generate_quiz(
        self,
        request: QuizGenerationRequest
    ):
        questions = self.ai_service.generate_quiz(request)

        return QuizGenerationResponse(
            success=True,
            message="สร้างข้อสอบสำเร็จ",
            questions=questions,
        )