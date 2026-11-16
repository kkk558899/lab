from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # 后端项目的根路径

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:123456@127.0.0.1:3306/lab_agent"
    JWT_SECRET_KEY: str = "sjQ9crUw71awph8ORnvERoUtMQ19qelECFjj06i1urz"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    LLM_API_KEY: str = "sk-c1934562b93d40a69cd0a1ee78fd20db"
    LLM_BASE_URL: str = "https://platform.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-flash"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
