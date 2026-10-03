from fastapi import APIRouter

from app.schemas.quiz_analysis import (
    QuizAnalysisRequest,
    QuizAnalysisResponse,
)

from app.services.quiz_analysis_service import (
    QuizAnalysisService
)


router = APIRouter(
    prefix="/api/quiz",
    tags=["Quiz Analysis"]
)


service = QuizAnalysisService()


@router.post(
    "/analyze",
    response_model=QuizAnalysisResponse
)
async def analyze_quiz(
    request: QuizAnalysisRequest
):

    data = await service.analyze_score(
        request
    )

    return QuizAnalysisResponse(

        success=True,

        message=
            "วิเคราะห์ผลการทำข้อสอบสำเร็จ",

        data=data
    )