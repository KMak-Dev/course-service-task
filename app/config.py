from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://course_app:course@localhost:5432/course_service"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
