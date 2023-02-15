from contextvars import ContextVar


ctx_client_id = ContextVar("client_id", default=None)
ctx_user_id = ContextVar("user_id", default=None)
