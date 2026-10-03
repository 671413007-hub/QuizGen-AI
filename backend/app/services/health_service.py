"""
Health Service
ทำหน้าที่ตรวจสอบสถานะความพร้อมของระบบ
"""

def get_system_health() -> dict:
    return {
        "status": "healthy",
        "message": "QuizGen AI Backend is running properly"
    }
