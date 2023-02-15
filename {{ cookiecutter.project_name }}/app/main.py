from fastapi import Depends, FastAPI, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import jwt
from sqlalchemy.orm import Session

from app import __version__, ctx_client_id, ctx_user_id
from app.config import get_jwks
from app.dependencies.auth import (
    verify_client_or_user_access_token,
    verify_user_access_token,
)
from app.dependencies.db import get_db
from app.routers import latest
from app.schemas.auth.jwt import JWT


TITLE = "{{ cookiecutter.friendly_name }}"
OPENAPI_URL = "/openapi.json"
FAVICON_URL = "/static/favicon.png"

app = FastAPI(
    # URLs specified as None here so we can add them manually below with auth.
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


def _decode_jwt(auth: str) -> JWT:
    """Decode access token without any of the checks to
    get the user and client info.
    """
    jwks = get_jwks()
    token_data = jwt.decode(
        auth,
        jwks,
        options={
            "verify_signature": False,
            "verify_aud": False,
            "verify_iat": False,
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iss": False,
            "verify_jti": False,
            "verify_at_hash": False,
            "require_sub": True,
        },
    )
    return JWT(**token_data)


@app.middleware("http")
async def add_user_auth_logging_header(request: Request, call_next):
    """Middleware function to log the request client ID and user ID
    in the access logs, via ContextVars.
    """
    client_creds = (
        request.headers.get("Authorization").split(" ")[1]
        if request.headers.get("Authorization")
        else None
    )
    user_creds = request.headers.get("x-amzn-oidc-accesstoken")
    if user_creds:
        token_data = _decode_jwt(user_creds)
        ctx_client_id.set(token_data.client_id)
        ctx_user_id.set(token_data.sub)
    elif client_creds:
        token_data = _decode_jwt(client_creds)
        ctx_client_id.set(token_data.client_id)
        ctx_user_id.set(token_data.sub)
    else:
        ctx_client_id.set("n/a")
        ctx_user_id.set("n/a")
    response = await call_next(request)
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=TITLE,
        version=__version__,
        description="'Tis the API for all things DATA.",
        routes=app.routes,
        tags=tags_metadata,
    )
    openapi_schema["info"]["x-logo"] = {"url": "/static/sylvera.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get(OPENAPI_URL, include_in_schema=False)
async def openapi(_=Depends(verify_client_or_user_access_token)):  # pragma: no cover
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
async def docs(_=Depends(verify_user_access_token)):  # pragma: no cover
    return get_swagger_ui_html(
        title=TITLE, openapi_url=OPENAPI_URL, swagger_favicon_url=FAVICON_URL
    )


@app.get("/redoc", include_in_schema=False)
async def redocs(_=Depends(verify_user_access_token)):  # pragma: no cover
    return get_redoc_html(
        title=TITLE, openapi_url=OPENAPI_URL, redoc_favicon_url=FAVICON_URL
    )


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    response_description="Health status",
)
def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """
    Checks the connection to DB and returns a JSON response.
    """
    is_database_working = True
    message = "DB connection successful!"
    status_code = status.HTTP_200_OK
    try:
        db.execute("SELECT 1;")
    except Exception as e:
        message = str(e)
        is_database_working = False
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    data = {"DB OK": is_database_working, "message": message}
    return JSONResponse(content=data, status_code=status_code)
