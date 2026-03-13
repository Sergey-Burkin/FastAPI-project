from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn, Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Shortener"
    VERSION: str = "1.0.0"
    
    POSTGRES_DSN: PostgresDsn = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/dbname",
        validation_alias='POSTGRES_DSN'
    )
    REDIS_DSN: RedisDsn = Field(
        default="redis://localhost:6379/0",
        validation_alias='REDIS_DSN'
    )
    SECRET_KEY: str = "change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    UNUSED_DAYS: int = 30  
    
    class Config:
        env_file = ".env"

settings = Settings()
print("Loaded settings:", settings.dict())