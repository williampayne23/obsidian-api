from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    vault_path: str = "/vault"


settings = Settings()
