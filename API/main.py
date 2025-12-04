import logging
from http.client import HTTPException

from fastapi import FastAPI
from loguru import logger
from starlette.responses import JSONResponse

from API.config import settings
from API import application
from API.infrastructure.database.models import Base
from API.infrastructure.database.session import engine, SESSION_MAKER
from API.presentation import rest, middleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from API.infrastructure.utils.tasks import add_vacation_days, check_work_period
from API.infrastructure.utils.hh_tasks import auto_analysis

# Adjust the logging
# -------------------------------

logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)
logger.add(
    "".join(
        [
            str(settings.root_dir),
            "/logs/",
            settings.logging.file.lower(),
            ".log",
        ]
    ),
    format=settings.logging.format,
    rotation=settings.logging.rotation,
    compression=settings.logging.compression,
    level="INFO",
)

# Adjust the application
# -------------------------------
app: FastAPI = application.create(
    debug=settings.debug_status,
    rest_routers=(
        rest.vacation.router,
        rest.recruiting.router
    ),
    middlewares=(
        middleware.db_session_middleware,
    ),
    startup_tasks=[],
    shutdown_tasks=[],
    docs_url="/docs", redoc_url=None
)
scheduler = AsyncIOScheduler(
         timezone='Asia/Aqtobe'
    )
scheduler.add_job(
    add_vacation_days,
    'cron',
    hour=10,
    minute=0,
    args=(SESSION_MAKER,)
)

scheduler.add_job(
    check_work_period,
    'cron',
    hour=10,
    minute=1,
    args=(SESSION_MAKER,)
)
# Для теста
scheduler.add_job(
    auto_analysis,
    'interval',
    minutes=59,
    args=(SESSION_MAKER,)
)


@app.on_event('startup')
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler.start()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Internal Server Error"}
    )
