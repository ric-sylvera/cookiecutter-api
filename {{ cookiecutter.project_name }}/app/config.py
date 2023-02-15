import os
from typing import Type

import httpx
from cachetools.func import ttl_cache

from app.schemas.errors.http import HTTPError


AUTH_ERROR_CODES = (401, 403)


def error_responses(
    *codes: int, include_auth_codes: bool = True
) -> dict[int | str, dict[str, Type[HTTPError]]]:
    # int | str needed in return type hint to stop mypy throwing a fit
    all_codes = codes + AUTH_ERROR_CODES if include_auth_codes else codes
    return {code: {"model": HTTPError} for code in all_codes}


class DBConfig:
    def __init__(self):
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.db = os.getenv("POSTGRES_DB")

    def get_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class MigrationsConfig(DBConfig):
    def __init__(self):
        super().__init__()
        self.user = os.getenv("MIGRATIONS_USER") or self.user
        self.password = os.getenv("MIGRATIONS_PASSWORD") or self.password


@ttl_cache(maxsize=1, ttl=60*60*24*7)
def get_jwks() -> dict[str, str]:
    response = httpx.get(
        f"https://cognito-idp.{os.environ.get('COGNITO_REGION')}.amazonaws.com/"
        f"{os.environ.get('COGNITO_USER_POOL_ID')}/.well-known/jwks.json"
    )
    return response.json()
