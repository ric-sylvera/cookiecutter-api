import logging
from copy import copy

from uvicorn.logging import DefaultFormatter  # type: ignore

from app import ctx_client_id, ctx_user_id
from app.main import app


class NewlineRemovingFormatter(DefaultFormatter):  # type: ignore
    """Replace newline characters with `\\n` in both the message and
    the exception description.
    """

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        msg = recordcopy.getMessage().strip().replace("\n", "\\n")
        recordcopy.__dict__["message"] = msg
        recordcopy.__dict__["exception"] = (
            recordcopy.exc_info[1].__repr__().strip().replace("\n", "\\n")
            if recordcopy.exc_info
            else ""
        )

        return super().formatMessage(recordcopy)  # type: ignore


class LogExtraFactory(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_id = ctx_client_id.get() or "N/A"
        user_id = ctx_user_id.get() or "N/A"

        self.__dict__["client_id"] = client_id
        self.__dict__["user_id"] = user_id


@app.on_event("startup")
async def startup_event():
    logging.setLogRecordFactory(LogExtraFactory)
