# @app.middleware('http')
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from API.infrastructure.database.session import get_session, db_session


async def db_session_middleware(request: Request, call_next):
    session: AsyncSession = await get_session()
    token = db_session.set(session)
    try:
        response = await call_next(request)
    finally:
        db_session.reset(token)
        await session.close()

    return response
