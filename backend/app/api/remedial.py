from fastapi import APIRouter

from app.schemas.remedial import (
    RemedialQuizRequest,
    RemedialQuizResponse,
)

from app.services.remedial_service import (
    RemedialQuizService
)


router = APIRouter(
    prefix="/api/quiz",
    tags=["Remedial Quiz"]
)


service = RemedialQuizService()


@router.post(
    "/remedial",
    response_model=RemedialQuizResponse
)
async def generate_remedial_quiz(
    request: RemedialQuizRequest
):

    questions = (
        await service.generate_remedial_quiz(
            request
        )
    )

    return RemedialQuizResponse(

        success=True,

        message=
            "สร้างข้อสอบสำหรับแก้จุดอ่อนสำเร็จ",

        weak_topics=
            request.weak_topics,

        questions=
            questions
    )