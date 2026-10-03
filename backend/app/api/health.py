from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_system_health


router = APIRouter(
    prefix="/api/health",
    tags=["Health"]
)


@router.get(
    "",
    response_model=HealthResponse
)
def check_health():
    """
    Endpoint สำหรับตรวจสอบสถานะของระบบ Backend
    """
    return get_system_health()