import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./video_generator.db"
    
    # API Keys (Mặc định để trống, sẽ lấy từ env hoặc cấu hình ở đây)
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" # Rachel default
    RUNWAY_API_KEY: str = ""
    KLING_API_KEY: str = ""
    ANIMAI_API_KEY: str = ""
    ANIMAI_BASE_URL: str = "https://ai.tool98.com"
    
    # Media paths
    STATIC_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    MEDIA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "media"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Tạo thư mục chứa media nếu chưa có
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_DIR, "audio"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_DIR, "video"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_DIR, "output"), exist_ok=True)
