from fastapi import Depends, HTTPException
from fastapi.openapi.models import HTTPBase as HTTPBaseModel
from fastapi.security import SecurityScopes
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.config import get_jwks
from app.schemas.auth.jwt import JWT


class XAmznOIDCAccesstoken(HTTPBase):
    def __init__(
        self,
        *,
        scheme_name: str | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ):
        self.model = HTTPBaseModel(
            scheme="bearer", bearerFormat="JWT", description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials: str = request.headers.get("x-amzn-oidc-accesstoken")
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme="", credentials=credentials)


http_auth = HTTPBearer(
    bearerFormat="JWT", auto_error=False, description="Client credentials flow"
)
x_amzn_oidc_auth = XAmznOIDCAccesstoken(
    auto_error=False,
    description=(
        "Auth code flow. Note, the credentials are not preceded by 'Bearer' "
        "but this still uses the same method"
    ),
)


def _verify_access_token(
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials,
    jwks: dict[str, str],
):
    if not credentials:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        token_data = jwt.decode(credentials.credentials, jwks)
    except JWTError:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED, detail="Could not validate credentials."
        )
    if set(security_scopes.scopes) - set(token_data["scope"].split()):
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access scope.",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
        )
    return JWT(**token_data)


def verify_client_or_user_access_token(
    client_credentials: HTTPAuthorizationCredentials = Depends(http_auth),
    user_credentials: HTTPAuthorizationCredentials = Depends(x_amzn_oidc_auth),
    jwks: dict[str, str] = Depends(get_jwks),
    security_scopes: SecurityScopes = SecurityScopes(),
) -> JWT:
    credentials = client_credentials or user_credentials
    return _verify_access_token(security_scopes, credentials, jwks)


def verify_client_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(http_auth),
    jwks: dict[str, str] = Depends(get_jwks),
    security_scopes: SecurityScopes = SecurityScopes(),
) -> JWT:
    return _verify_access_token(security_scopes, credentials, jwks)


def verify_user_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(x_amzn_oidc_auth),
    jwks: dict[str, str] = Depends(get_jwks),
    security_scopes: SecurityScopes = SecurityScopes(),
) -> JWT:
    return _verify_access_token(security_scopes, credentials, jwks)
