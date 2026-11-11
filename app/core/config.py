from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    APP_NAME: str = "ShopEase User Management Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "shopease_user_db"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_USER_ID_CLAIM: str = "sub"
    AUTH_SERVICE_URL: str = "http://localhost:8001"

    @property
    def DATABASE_URL(self) -> str:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
