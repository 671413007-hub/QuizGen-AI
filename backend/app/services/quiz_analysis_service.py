from collections import Counter
from typing import List

from fastapi.concurrency import run_in_threadpool

from app.schemas.quiz_analysis import (
    QuizAnalysisRequest,
    QuizAnalysisResponseData,
    WrongQuestion,
    WeakTopic,
)

from app.services.ai_service import AIServiceFactory


class QuizAnalysisService:

    def __init__(self):
        self.ai_service = AIServiceFactory.get_service()

    async def analyze_score(
        self,
        request: QuizAnalysisRequest
    ) -> QuizAnalysisResponseData:

        total_questions = len(request.questions)

        correct_count = 0

        wrong_questions: List[WrongQuestion] = []

        topic_counter = Counter()

        # =========================================
        # 1. ตรวจคำตอบ
        # =========================================

        for index, item in enumerate(
            request.questions,
            start=1
        ):

            user_answer = item.user_answer.strip()

            correct_answer = item.answer.strip()

            is_correct = (
                user_answer.lower()
                == correct_answer.lower()
            )

            if is_correct:

                correct_count += 1

            else:

                wrong_questions.append(
                    WrongQuestion(
                        question_index=index,
                        question=item.question,
                        user_answer=item.user_answer,
                        correct_answer=item.answer,
                        topic=item.topic,
                        explanation=item.explanation,
                    )
                )

                topic_counter[item.topic] += 1

        # =========================================
        # 2. คำนวณคะแนน
        # =========================================

        wrong_count = (
            total_questions
            - correct_count
        )

        score_percentage = round(
            (correct_count / total_questions) * 100,
            2
        )

        # =========================================
        # 3. ถ้ามีข้อผิด
        #    ส่งให้ AI วิเคราะห์
        # =========================================

        if wrong_questions:

            weak_topic_names = list(
                topic_counter.keys()
            )

            wrong_questions_data = [

                {
                    "question_index":
                        item.question_index,

                    "question":
                        item.question,

                    "user_answer":
                        item.user_answer,

                    "correct_answer":
                        item.correct_answer,

                    "topic":
                        item.topic,

                    "explanation":
                        item.explanation,
                }

                for item in wrong_questions
            ]

            ai_analysis = await run_in_threadpool(
                self.ai_service.analyze_weaknesses,
                wrong_questions_data,
                weak_topic_names
            )

        else:

            ai_analysis = {

                "weak_topics": [],

                "overall_analysis":
                    "ผู้เรียนตอบถูกทุกข้อ "
                    "ยังไม่พบหัวข้อที่เป็นจุดอ่อน",

                "study_recommendations": [

                    "สามารถศึกษาบทเรียน "
                    "ในระดับที่ยากขึ้นได้"
                ]
            }

        # =========================================
        # 4. แปลงผล AI เป็น Schema
        # =========================================

        weak_topics = []

        for topic in ai_analysis.get(
            "weak_topics",
            []
        ):

            topic_name = topic.get(
                "topic",
                ""
            )

            if not topic_name:
                continue

            weak_topics.append(

                WeakTopic(

                    topic=topic_name,

                    wrong_count=
                        topic_counter.get(
                            topic_name,
                            0
                        ),

                    reason=
                        topic.get(
                            "reason",
                            "พบข้อผิดในหัวข้อนี้"
                        ),

                    recommendation=
                        topic.get(
                            "recommendation",

                            f"ควรทบทวนเรื่อง "
                            f"{topic_name}"
                        )
                )
            )

        # =========================================
        # 5. ส่งผลลัพธ์กลับ
        # =========================================

        return QuizAnalysisResponseData(

            total_questions=
                total_questions,

            correct_count=
                correct_count,

            wrong_count=
                wrong_count,

            score_percentage=
                score_percentage,

            wrong_questions=
                wrong_questions,

            weak_topics=
                weak_topics,

            overall_analysis=
                ai_analysis.get(
                    "overall_analysis",
                    ""
                ),

            study_recommendations=
                ai_analysis.get(
                    "study_recommendations",
                    []
                )
        )