import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    AI_PROVIDER: str = os.getenv(
        "AI_PROVIDER",
        "mock"
    )

    THAILLM_API_KEY: str = os.getenv(
        "THAILLM_API_KEY",
        ""
    )

    THAILLM_BASE_URL: str = os.getenv(
        "THAILLM_BASE_URL",
        "https://api.thaillm.or.th/v1"
    )

    THAILLM_MODEL: str = os.getenv(
        "THAILLM_MODEL",
        "OpenThaiGPT-ThaiLLM-8B-Instruct-v7.2"
    )

    THAILLM_TIMEOUT_SECONDS: int = int(
        os.getenv(
            "THAILLM_TIMEOUT_SECONDS",
            "60"
        )
    )


settings = Settings()