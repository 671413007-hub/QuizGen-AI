import json
import logging
import re
from abc import ABC, abstractmethod
from typing import List
import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.schemas.quiz import QuizGenerationRequest, Question, QuizGenerationResponse
from app.core.config import settings

# ตั้งค่า Logging ปลอดภัย ไม่ log secret หรือ api key
logger = logging.getLogger("quizgen.ai")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class BaseAIService(ABC):
    """
    Interface หลักสำหรับ AI Service Provider
    """
    @abstractmethod
    def generate_quiz(self, request: QuizGenerationRequest) -> List[Question]:
        """
        รับ QuizGenerationRequest และส่งคืนรายการคำถาม List[Question]
        """
        pass

    @abstractmethod
    def analyze_weaknesses(self, wrong_questions_data: list, weak_topics: list) -> dict:
        """
        รับข้อมูลข้อที่ตอบผิดและรายการหัวข้อ เพื่อให้ AI วิเคราะห์จุดอ่อนและให้คำแนะนำ
        คืนค่า dict ที่ตรงกับ AIAnalysisResult Schema
        """
        pass


class MockAIService(BaseAIService):
    """
    Mock AI Service สำหรับทดสอบระบบ Data Flow โดยไม่ต่อ API ภายนอก
    """
    def generate_quiz(self, request: QuizGenerationRequest) -> List[Question]:
        logger.info("Calling MockAIService")
        content_preview = request.content.strip()
        if len(content_preview) > 30:
            content_preview = content_preview[:30] + "..."

        questions: List[Question] = []

        for i in range(1, request.question_count + 1):
            if request.question_type == "multiple-choice":
                options = [
                    f"ก. ข้อสรุปที่ถูกต้องตามเนื้อหาบทเรียนส่วนที่ {i}",
                    f"ข. ข้อความที่ไม่ตรงกับความเป็นจริงเกี่ยวกับ {content_preview}",
                    f"ค. การตีความที่ไม่เกี่ยวข้องกับหัวข้อ",
                    f"ง. ไม่มีข้อใดถูก"
                ]
                answer = options[0]
                question_text = f"ข้อที่ {i}: จากเนื้อหา '{content_preview}' ข้อใดคือใจความสำคัญที่ถูกต้องที่สุด? (ระดับ: {request.difficulty})"
                explanation = f"ตัวเลือก '{answer}' ถูกต้อง เพราะสอดคล้องกับเนื้อหาบทเรียนที่ระบุไว้ในส่วนที่ {i}"

            elif request.question_type == "true-false":
                options = ["ถูก", "ผิด"]
                answer = "ถูก" if i % 2 != 0 else "ผิด"
                question_text = f"ข้อที่ {i}: ข้อความต่อไปนี้ถูกต้องหรือไม่เกี่ยวกับ '{content_preview}'? (ระดับ: {request.difficulty})"
                explanation = f"คำตอบคือ '{answer}' ตามข้อมูลที่ปรากฏในบทเรียน"

            else:  # short-answer
                options = []
                answer = f"คำตอบสั้นที่ {i}"
                question_text = f"ข้อที่ {i}: จงอธิบายความหมายสั้น ๆ เกี่ยวกับสาระสำคัญของ '{content_preview}' (ระดับ: {request.difficulty})"
                explanation = f"คำตอบที่ถูกต้องคือ '{answer}' จากการวิเคราะห์เนื้อหา"

            questions.append(
                Question(
                    question=question_text,
                    options=options,
                    answer=answer,
                    explanation=explanation,
                    topic=f"หัวข้อบทเรียนที่ {((i - 1) % 3) + 1}"
                )
            )

        logger.info("MockAIService generated %d questions successfully", len(questions))
        return questions

    def analyze_weaknesses(self, wrong_questions_data: list, weak_topics: list) -> dict:
        logger.info("Calling MockAIService.analyze_weaknesses with %d wrong questions", len(wrong_questions_data))
        topic_analysis = []
        for t in weak_topics:
            topic_analysis.append({
                "topic": t,
                "reason": f"ผู้เรียนอาจยังสับสนในหลักการสำคัญของหัวข้อ '{t}'",
                "recommendation": f"ควรทบทวนนิยามและดูตัวอย่างการประยุกต์ใช้งานของหัวข้อ '{t}' เพิ่มเติม"
            })

        return {
            "weak_topics": topic_analysis,
            "overall_analysis": f"ผู้เรียนมีความเข้าใจในภาพรวมระดับปานกลาง แต่ยังมีจุดที่ต้องทบทวนในหัวข้อ: {', '.join(weak_topics)}",
            "study_recommendations": [
                "อ่านทบทวนสรุปใจความสำคัญของหัวข้อที่ตอบผิดอย่างละเอียด",
                "ลองฝึกทำข้อสอบซ้ำเฉพาะหัวข้อที่มีข้อผิดพลาด"
            ]
        }


class ThaiLLMService(BaseAIService):
    """
    ThaiLLM Provider Service
    เรียกใช้งาน ThaiLLM ผ่าน OpenAI-compatible API endpoint
    """
    def generate_quiz(self, request: QuizGenerationRequest) -> List[Question]:
        api_key = settings.THAILLM_API_KEY
        if not api_key or api_key.strip() in ("", "your_actual_thaillm_api_key_here", "ใส่_API_KEY_ของผู้ใช้ตรงนี้"):
            logger.error("ThaiLLM API key is missing or not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ไม่พบ THAILLM_API_KEY หรือยังไม่ได้กำหนดค่าในระบบ กรุณาตรวจสอบไฟล์ .env ใน backend"
            )

        endpoint_url = f"{settings.THAILLM_BASE_URL}/chat/completions"
        logger.info("Calling ThaiLLM provider at model: %s", settings.THAILLM_MODEL)

        prompt = self._build_prompt(request)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": settings.THAILLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "คุณคือผู้เชี่ยวชาญด้านการศึกษาและการสร้างแบบทดสอบภาษาไทย "
                        "จงสร้างแบบทดสอบตามเนื้อหาและเงื่อนไขที่กำหนด โดยตอบกลับเป็นรูปแบบ JSON ล้วนเท่านั้น "
                        "ห้ามใส่ข้อความเกริ่นนำหรือคำอธิบายอื่นนอกเหนือจาก JSON block"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5
        }

        try:
            with httpx.Client(timeout=settings.THAILLM_TIMEOUT_SECONDS) as client:
                response = client.post(endpoint_url, headers=headers, json=payload)
        except httpx.TimeoutException:
            logger.error("ThaiLLM API request timed out after %s seconds", settings.THAILLM_TIMEOUT_SECONDS)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"ThaiLLM API ใช้เวลาตอบสนองเกินกำหนด ({settings.THAILLM_TIMEOUT_SECONDS} วินาที)"
            )
        except httpx.RequestError as exc:
            logger.error("Network or connection error while contacting ThaiLLM: %s", exc.__class__.__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ไม่สามารถเชื่อมต่อไปยังเซิร์ฟเวอร์ ThaiLLM ได้: {exc.__class__.__name__}"
            )

        if response.status_code == 401 or response.status_code == 403:
            logger.error("ThaiLLM authentication failed (status: %d)", response.status_code)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="การยืนยันตัวตนกับ ThaiLLM ไม่สำเร็จ: THAILLM_API_KEY ไม่ถูกต้องหรือหมดอายุ"
            )
        elif response.status_code != 200:
            logger.error("ThaiLLM API returned HTTP error: %d", response.status_code)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ThaiLLM API ตอบกลับข้อผิดพลาด HTTP {response.status_code}"
            )

        # แกะผลลัพธ์จาก Chat Completions
        try:
            response_json = response.json()
        except Exception as exc:
            logger.error("Failed to decode ThaiLLM response as JSON: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="เซิร์ฟเวอร์ ThaiLLM ตอบกลับข้อมูลที่ไม่ใช่ JSON"
            )

        # Diagnostic log แบบปลอดภัยสำหรับ envelope
        choices = response_json.get("choices")
        logger.info(
            "ThaiLLM envelope diagnostic: status=%d, keys=%s, choices_type=%s, choices_len=%s",
            response.status_code,
            list(response_json.keys()),
            type(choices).__name__,
            len(choices) if isinstance(choices, list) else "N/A"
        )

        try:
            if not isinstance(choices, list) or len(choices) == 0:
                raise KeyError("choices is empty or not a list")

            first_choice = choices[0]
            message = first_choice.get("message") if isinstance(first_choice, dict) else None
            
            logger.info(
                "ThaiLLM message diagnostic: choice_type=%s, message_type=%s",
                type(first_choice).__name__,
                type(message).__name__
            )

            if not isinstance(message, dict):
                raise KeyError("message is missing or not a dict")

            raw_content = message.get("content")

            logger.info(
                "ThaiLLM raw content metadata: type=%s, length=%d",
                type(raw_content).__name__,
                len(raw_content) if isinstance(raw_content, str) else -1
            )

            # Log raw_content preview แบบปลอดภัย (repr) ไม่เกิน 2000 ตัวอักษร
            logger.info(
                "ThaiLLM raw content preview: %r",
                raw_content[:2000] if isinstance(raw_content, str) else raw_content
            )

        except (KeyError, IndexError, ValueError, TypeError) as exc:
            logger.error("Failed to parse ThaiLLM response envelope: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="โครงสร้างการตอบกลับจาก ThaiLLM API ไม่ถูกต้อง"
            )

        if not isinstance(raw_content, str):
            logger.error("ThaiLLM message content is not a string (type=%s)", type(raw_content).__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"เนื้อหาที่ได้รับจาก ThaiLLM ไม่ใช่ข้อความสตริง (ประเภท: {type(raw_content).__name__})"
            )

        # สกัดและแปลง JSON ที่ AI สร้างออกมา
        return self._parse_and_validate_questions(raw_content, request)

    def _build_prompt(self, request: QuizGenerationRequest) -> str:
        type_str = {
            "multiple-choice": "ปรนัย 4 ตัวเลือก (Multiple Choice) โดยต้องมี options ครบ 4 ตัวเลือก และ answer ต้องตรงกับตัวเลือกใดตัวเลือกหนึ่งอย่างแน่นอน",
            "true-false": "ถูก / ผิด (True / False) โดย options มี 2 ตัวเลือกคือ ['ถูก', 'ผิด'] และ answer ต้องเป็น 'ถูก' หรือ 'ผิด'",
            "short-answer": "ตอบคำถามสั้น (Short Answer) โดย options เป็นรายการว่าง [] และ answer เป็นคำตอบสรุปสั้นๆ"
        }.get(request.question_type, "ปรนัย 4 ตัวเลือก")

        diff_str = {
            "easy": "ง่าย (เน้นความจำและความเข้าใจเบื้องต้น)",
            "medium": "ปานกลาง (เน้นการคิดวิเคราะห์และการประยุกต์ใช้)",
            "hard": "ยาก (เน้นการวิเคราะห์เชิงลึกและการสังเคราะห์)"
        }.get(request.difficulty, "ปานกลาง")

        prompt = f"""
กรุณาสร้างแบบทดสอบภาษาไทยจำนวน {request.question_count} ข้อ จากเนื้อหาบทเรียนด้านล่างนี้:

[เนื้อหาบทเรียน]
\"\"\"
{request.content}
\"\"\"

[เงื่อนไขข้อสอบ]
1. จำนวนข้อสอบ: {request.question_count} ข้อ
2. ประเภทข้อสอบ: {type_str}
3. ระดับความยาก: {diff_str}
4. แต่ละข้อต้องประกอบด้วย:
   - question: คำถามภาษาไทยที่ชัดเจน
   - options: รายการตัวเลือก (สำหรับปรนัยต้องมี 4 ตัวเลือกเสมอ)
   - answer: คำตอบที่ถูกต้อง (ต้องตรงกับข้อความใน options เป๊ะๆ สำหรับปรนัย)
   - explanation: คำอธิบายเฉลยเหตุผลว่าทำไมคำตอบนี้จึงถูกต้องตามเนื้อหา
   - topic: หัวข้อย่อยหรือสาระสำคัญที่ข้อนี้ใช้วัดความรู้

ตอบกลับเป็นโครงสร้าง JSON รูปแบบนี้เท่านั้น:
{{
  "questions": [
    {{
      "question": "คำถามข้อที่ 1",
      "options": ["ตัวเลือก 1", "ตัวเลือก 2", "ตัวเลือก 3", "ตัวเลือก 4"],
      "answer": "ตัวเลือก 1",
      "explanation": "คำอธิบายเหตุผลของข้อที่ 1",
      "topic": "หัวข้อบทเรียน"
    }}
  ]
}}
"""
        return prompt.strip()

    def _parse_and_validate_questions(self, raw_text: str, request: QuizGenerationRequest) -> List[Question]:
        if not raw_text or not raw_text.strip():
            logger.error("AI response content is empty")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI ส่งเนื้อหาว่างเปล่ากลับมา"
            )

        # 1. ตัดแท็ก Reasoning / CoT เช่น <think>...</think> ที่โมเดลสร้างออกมา
        cleaned_text = re.sub(r"<think>[\s\S]*?</think>", "", raw_text, flags=re.DOTALL).strip()

        # 2. ค้นหาบล็อก JSON ใน Markdown ```json ... ``` ถ้ามี
        json_code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text)
        if json_code_match:
            candidate_json = json_code_match.group(1).strip()
        else:
            # หากไม่มี Markdown block ให้ค้นหาขอบเขต JSON ตั้งแต่ { ตัวแรก ถึง } ตัวสุดท้าย
            first_brace = cleaned_text.find("{")
            last_brace = cleaned_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate_json = cleaned_text[first_brace:last_brace + 1].strip()
            else:
                candidate_json = cleaned_text

        # Diagnostic log แบบปลอดภัยสำหรับ candidate_json
        logger.info(
            "JSON candidate metadata: length=%d",
            len(candidate_json)
        )
        logger.info(
            "JSON candidate preview: %r",
            candidate_json[:2000]
        )

        if not candidate_json:
            logger.error("candidate_json became empty after extraction from raw_text (length=%d)", len(raw_text))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ไม่สามารถสกัดข้อมูล JSON จากผลลัพธ์ของ AI ได้"
            )

        # 3. แปลงเป็น JSON object
        try:
            parsed_data = json.loads(candidate_json)
        except json.JSONDecodeError as exc:
            logger.error("AI returned malformed JSON: %s (Candidate preview: %r)", exc, candidate_json[:200])
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI ส่งผลลัพธ์กลับมาในรูปแบบที่ไม่ใช่ JSON ที่ถูกต้อง: {exc.msg}"
            )

        # 4. ตรวจสอบโครงสร้างว่ามีคีย์ questions
        if not isinstance(parsed_data, dict) or "questions" not in parsed_data:
            logger.error("Parsed JSON does not contain 'questions' list")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ผลลัพธ์จาก AI ไม่มีรายการ 'questions' ตามข้อกำหนด"
            )

        raw_questions = parsed_data["questions"]
        if not isinstance(raw_questions, list) or len(raw_questions) == 0:
            logger.error("Questions list is empty or not a list")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI ไม่ส่งข้อสอบกลับมา หรือส่งรายการข้อสอบว่างเปล่า"
            )

        # 5. Pydantic Validation ทีละข้อ พร้อมตรวจสอบกฎข้อสอบ
        validated_questions: List[Question] = []
        for idx, item in enumerate(raw_questions):
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ข้อสอบข้อที่ {idx + 1} ไม่ได้อยู่ในรูปแบบ Object ที่ถูกต้อง"
                )

            # ตรวจสอบ field จำเป็นเบื้องต้น
            for field in ["question", "answer", "explanation", "topic"]:
                if not item.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"ข้อสอบข้อที่ {idx + 1} ขาดข้อมูลฟิลด์ '{field}' หรือมีค่าว่าง"
                    )

            try:
                question_obj = Question(**item)
            except ValidationError as val_err:
                logger.error("Question at index %d failed validation: %s", idx, val_err)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ข้อสอบข้อที่ {idx + 1} จาก AI มีโครงสร้างไม่ตรงตาม Schema"
                )

            # ตรวจสอบกฎเฉพาะสำหรับ multiple-choice
            if request.question_type == "multiple-choice":
                # ปรับแต่ง/เติมให้ครบ 4 ตัวเลือกกรณีที่ AI ตอบขาดหรือเกินเล็กน้อย
                if len(question_obj.options) < 4:
                    if question_obj.answer not in question_obj.options:
                        question_obj.options.append(question_obj.answer)
                    while len(question_obj.options) < 4:
                        question_obj.options.append(f"ตัวเลือกเพิ่มเติมที่ {len(question_obj.options) + 1}")
                elif len(question_obj.options) > 4:
                    # ตัดเหลือ 4 โดยต้องรักษาตัวเลือกที่เป็น answer ไว้
                    if question_obj.answer in question_obj.options[:4]:
                        question_obj.options = question_obj.options[:4]
                    else:
                        question_obj.options = question_obj.options[:3] + [question_obj.answer]

                # รับประกันว่า answer ต้องอยู่ใน options เสมอ
                if question_obj.answer not in question_obj.options:
                    question_obj.options[0] = question_obj.answer

            validated_questions.append(question_obj)

        logger.info(
            "Successfully validated %d questions (requested: %d) from ThaiLLM",
            len(validated_questions),
            request.question_count
        )
        return validated_questions

    def analyze_weaknesses(self, wrong_questions_data: list, weak_topics: list) -> dict:
        """
        ส่งเฉพาะข้อมูลข้อที่ตอบผิดและหัวข้อไปให้ ThaiLLM วิเคราะห์จุดอ่อนและให้คำแนะนำ
        """
        api_key = settings.THAILLM_API_KEY
        if not api_key or api_key.strip() in ("", "your_actual_thaillm_api_key_here", "ใส่_API_KEY_ของผู้ใช้ตรงนี้"):
            logger.error("ThaiLLM API key is missing or not configured for weakness analysis")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ไม่พบ THAILLM_API_KEY สำหรับการวิเคราะห์จุดอ่อน กรุณาตรวจสอบไฟล์ .env"
            )

        endpoint_url = f"{settings.THAILLM_BASE_URL}/chat/completions"
        logger.info("Calling ThaiLLM for weakness analysis. Topics count: %d, Wrong questions: %d", len(weak_topics), len(wrong_questions_data))

        # สร้าง Context ของข้อที่ตอบผิด
        items_desc = []
        for item in wrong_questions_data:
            items_desc.append(
                f"- ข้อที่ {item['question_index']} (หัวข้อ: {item['topic']})\n"
                f"  คำถาม: {item['question']}\n"
                f"  คำตอบที่ผู้เรียนตอบ: {item['user_answer']}\n"
                f"  คำตอบที่ถูกต้อง: {item['correct_answer']}\n"
                f"  คำอธิบาย: {item['explanation']}"
            )
        wrong_summary = "\n\n".join(items_desc)

        prompt = f"""
คุณคือผู้เชี่ยวชาญด้านการประเมินการเรียนรู้และการวิเคราะห์จุดอ่อนของผู้เรียน
ผู้เรียนเพิ่งทำแบบทดสอบเสร็จ และมีข้อที่ตอบผิดในหัวข้อต่อไปนี้:
หัวข้อที่ตอบผิด: {', '.join(weak_topics)}

รายละเอียดข้อที่ตอบผิด:
\"\"\"
{wrong_summary}
\"\"\"

จงวิเคราะห์จุดอ่อนของผู้เรียน โดยระบุ:
1. weak_topics: รายการวิเคราะห์แยกตามหัวข้อที่ตอบผิด แต่ละหัวข้อประกอบด้วย:
   - topic: ชื่อหัวข้อ
   - reason: สาเหตุเชิงเนื้อหาหรือมโนทัศน์ที่คาดว่าผู้เรียนน่าจะเข้าใจผิดหรือสับสน
   - recommendation: คำแนะนำเฉพาะเจาะจงในการทบทวนหัวข้อนี้
2. overall_analysis: สรุปภาพรวมจุดอ่อนของผู้เรียน และแนวโน้มความเข้าใจในวิชานี้
3. study_recommendations: รายการคำแนะนำและขั้นตอนการอ่านทบทวนที่เป็นรูปธรรม (อย่างน้อย 2-3 ข้อ)

ตอบกลับเป็นโครงสร้าง JSON รูปแบบนี้เท่านั้น:
{{
  "weak_topics": [
    {{
      "topic": "ชื่อหัวข้อ",
      "reason": "สาเหตุเชิงเนื้อหาที่เข้าใจผิด...",
      "recommendation": "คำแนะนำการทบทวน..."
    }}
  ],
  "overall_analysis": "ภาพรวมการวิเคราะห์...",
  "study_recommendations": [
    "คำแนะนำข้อที่ 1...",
    "คำแนะนำข้อที่ 2..."
  ]
}}
"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": settings.THAILLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์การเรียนรู้ จงวิเคราะห์จุดอ่อนของผู้เรียนและตอบกลับเป็น JSON ล้วนเท่านั้น"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5
        }

        try:
            with httpx.Client(timeout=settings.THAILLM_TIMEOUT_SECONDS) as client:
                response = client.post(endpoint_url, headers=headers, json=payload)
        except httpx.TimeoutException:
            logger.error("ThaiLLM weakness analysis request timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="ThaiLLM API ใช้เวลาวิเคราะห์จุดอ่อนนานเกินกำหนด"
            )
        except httpx.RequestError as exc:
            logger.error("Connection error during ThaiLLM weakness analysis: %s", exc.__class__.__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ไม่สามารถเชื่อมต่อไปยัง ThaiLLM ได้: {exc.__class__.__name__}"
            )

        if response.status_code != 200:
            logger.error("ThaiLLM weakness analysis returned HTTP %d", response.status_code)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ThaiLLM API ตอบกลับข้อผิดพลาด HTTP {response.status_code}"
            )

        try:
            response_json = response.json()
            raw_content = response_json["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("Failed to parse ThaiLLM weakness response envelope: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="โครงสร้างการตอบกลับจาก ThaiLLM ในการวิเคราะห์จุดอ่อนไม่ถูกต้อง"
            )

        # สกัด JSON จาก raw_content (ตัด <think> และ markdown code blocks)
        cleaned_text = re.sub(r"<think>[\s\S]*?</think>", "", raw_content, flags=re.DOTALL).strip()
        json_code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text)
        if json_code_match:
            candidate_json = json_code_match.group(1).strip()
        else:
            first_brace = cleaned_text.find("{")
            last_brace = cleaned_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate_json = cleaned_text[first_brace:last_brace + 1].strip()
            else:
                candidate_json = cleaned_text

        try:
            parsed_analysis = json.loads(candidate_json)
        except json.JSONDecodeError as exc:
            logger.error("AI returned malformed JSON during weakness analysis: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI ส่งผลการวิเคราะห์จุดอ่อนกลับมาในรูปแบบที่ไม่ใช่ JSON: {exc.msg}"
            )

        logger.info("ThaiLLM weakness analysis completed successfully")
        return parsed_analysis


class AIForThaiService(BaseAIService):
    """
    Adapter สำหรับ AI for Thai API (เตรียมไว้สำหรับอนาคต)
    """
    def generate_quiz(self, request: QuizGenerationRequest) -> List[Question]:
        raise NotImplementedError("AI for Thai Service ยังไม่ได้เปิดใช้งานในขั้นตอนนี้")

    def analyze_weaknesses(self, wrong_questions_data: list, weak_topics: list) -> dict:
        raise NotImplementedError("AI for Thai Service ยังไม่ได้เปิดใช้งานในขั้นตอนนี้")


class AIServiceFactory:
    """
    Factory สำหรับเลือก AI Service Provider
    รองรับการอ่านค่าจาก settings.AI_PROVIDER
    """
    @staticmethod
    def get_service(provider: str = None) -> BaseAIService:
        if not provider:
            provider = settings.AI_PROVIDER

        provider_lower = provider.lower() if provider else "mock"
        if provider_lower == "thaillm":
            return ThaiLLMService()
        elif provider_lower == "aiforthai":
            return AIForThaiService()
        return MockAIService()
