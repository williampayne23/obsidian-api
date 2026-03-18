from functools import lru_cache

from app.config import settings
from app.services.vault import VaultService


@lru_cache
def get_vault() -> VaultService:
    return VaultService(settings.vault_path)
