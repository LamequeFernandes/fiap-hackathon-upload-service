from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://upload_user:upload_pass@localhost:5432/upload_db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "diagrams"
    minio_secure: bool = False
    max_file_size_mb: int = 10
    service_name: str = "upload-service"
    log_level: str = "INFO"
    rabbitmq_exchange: str = "arch_analyzer"
    rabbitmq_queue: str = "analysis.process"
    rabbitmq_routing_key: str = "analysis.process"

    model_config = {"env_file": ".env"}


settings = Settings()
