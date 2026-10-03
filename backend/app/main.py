from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import (
    router as health_router
)

from app.api.quiz import (
    router as quiz_router
)

from app.api.quiz_analysis import (
    router as quiz_analysis_router
)

from app.api.remedial import (
    router as remedial_router
)


app = FastAPI(

    title="QuizGen AI API",

    description=(
        "ระบบสร้าง วิเคราะห์ "
        "และปรับข้อสอบด้วย AI"
    ),

    version="1.0.0"
)


# =========================================
# CORS
# =========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================
# Routers
# =========================================

app.include_router(
    health_router
)

app.include_router(
    quiz_router
)

app.include_router(
    quiz_analysis_router
)

app.include_router(
    remedial_router
)


# =========================================
# Root
# =========================================

@app.get("/")
def root():

    return {

        "name":
            "QuizGen AI",

        "message":
            "QuizGen AI Backend is running",

        "version":
            "1.0.0"
    }
