from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Knowledge Platform"
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    secret_key: str = "change-me"

    frontend_url: str = "http://localhost:3000"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_knowledge"
    redis_url: str = "redis://localhost:6379/0"

    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openai_api_key: str = ""
    vllm_base_url: str = "http://localhost:8001/v1"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "text-embedding-004"

    max_file_size_mb: int = 25
    allowed_file_types: str = "pdf,docx,txt"

    aws_region: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket_name: str = ""
    sqs_queue_url: str = ""

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
