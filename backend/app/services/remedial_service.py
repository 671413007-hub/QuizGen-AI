from fastapi.concurrency import run_in_threadpool

from app.schemas.quiz import QuizGenerationRequest

from app.schemas.remedial import (
    RemedialQuizRequest
)

from app.services.ai_service import (
    AIServiceFactory
)


class RemedialQuizService:

    def __init__(self):

        self.ai_service = (
            AIServiceFactory.get_service()
        )

    async def generate_remedial_quiz(
        self,
        request: RemedialQuizRequest
    ):

        weak_topics_text = ", ".join(
            request.weak_topics
        )

        remedial_content = f"""
คุณกำลังสร้างข้อสอบสำหรับแก้จุดอ่อนของผู้เรียน

เนื้อหาบทเรียนต้นฉบับ:
{request.original_content}

หัวข้อที่ผู้เรียนยังมีจุดอ่อน:
{weak_topics_text}

ข้อกำหนดในการสร้างข้อสอบ:

1. ต้องเน้นหัวข้อที่ผู้เรียนยังมีจุดอ่อน
2. ต้องอ้างอิงจากเนื้อหาบทเรียนต้นฉบับ
3. ต้องไม่สร้างคำถามที่อยู่นอกเนื้อหา
4. ต้องวัดความเข้าใจของผู้เรียน
5. ควรใช้คำถามที่แตกต่างจากข้อสอบเดิม
6. ทุกข้อมีคำตอบที่ถูกต้อง
7. ทุกข้อมีคำอธิบาย
8. ระดับความยาก: {request.difficulty}

จุดประสงค์:
ต้องการให้ผู้เรียนฝึกซ้ำเฉพาะเรื่องที่ยังไม่เข้าใจ
"""

        quiz_request = QuizGenerationRequest(

            content=
                remedial_content.strip(),

            question_count=
                request.question_count,

            question_type=
                "multiple-choice",

            difficulty=
                request.difficulty
        )

        questions = await run_in_threadpool(

            self.ai_service.generate_quiz,

            quiz_request
        )

        return questions