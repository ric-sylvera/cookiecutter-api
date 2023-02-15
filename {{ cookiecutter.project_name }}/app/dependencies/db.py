from sqlalchemy.orm import Session

from app.db.base import get_sessionlocal


async def get_db() -> Session:
    """ Creates a local DB session object.

    Returns:
        DB session object
    """
    Session = get_sessionlocal()
    async with Session.begin() as session:
        yield session
