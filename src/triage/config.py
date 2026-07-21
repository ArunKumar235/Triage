from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Triage"
    environment: str = "development"

    database_url: str
    webhook_shared_secret: str

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = False 
    notification_from_email: str = "no-reply@triage.com"

    kafka_bootstrap_servers: str
    
    kafka_topic_testable_ready_for_testing: str
    kafka_topic_member_availability_changed: str
    kafka_topic_assignment_completed: str

    kafka_topic_testable_ready_for_testing_dlq: str
    kafka_topic_member_availability_changed_dlq: str
    kafka_topic_assignment_completed_dlq: str

    orchestrator_model: str

    vector_store_path: str
    embedding_model: str
    
    langchain_tracing_v2: str = "false"
    langchain_api_key: str | None = None
    langchain_project: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False)

@lru_cache
def get_settings() -> Settings:
    return Settings()
