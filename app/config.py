from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    vault_path: str = "/vault"
    redis_host: str = ""
    redis_port: int = 6379
    redis_password: str = ""


settings = Settings()
