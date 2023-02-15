from pydantic import BaseModel


class JWT(BaseModel):
    auth_time: int
    client_id: str
    exp: int
    iat: int
    iss: str
    jti: str
    scope: str
    sub: str
    token_use: str
    version: int
