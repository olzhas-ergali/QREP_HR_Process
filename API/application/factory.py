import asyncio
from functools import partial
from typing import Callable, Coroutine, Iterable

from fastapi import APIRouter, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

__all__ = ("create",)


def create(
    *_,
    rest_routers: Iterable[APIRouter],
    startup_tasks: Iterable[Callable[[], Coroutine]] | None = None,
    shutdown_tasks: Iterable[Callable[[], Coroutine]] | None = None,
    middlewares: Iterable[Callable[[], Coroutine]] | None = None,
    **kwargs,
) -> FastAPI:
    """The application factory using FastAPI framework.
    🎉 Only passing routes is mandatory to start.
    """

    # Initialize the base FastAPI application
    app = FastAPI(**kwargs)

    for middleware in middlewares:
        app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)

    # Include REST API routers
    for router in rest_routers:
        app.include_router(router)

    # Define startup tasks that are running asynchronous using FastAPI hook
    if startup_tasks:
        for task in startup_tasks:
            coro = partial(asyncio.create_task, task())
            app.on_event("startup")(coro)

    # Define shutdown tasks using FastAPI hook
    if shutdown_tasks:
        for task in shutdown_tasks:
            app.on_event("shutdown")(task)

    return app
