from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException

from mood_diary.backend.database.db import init_db
from mood_diary.backend.exceptions.base import BaseApplicationException
from mood_diary.backend.routes.auth import router as auth_router
from mood_diary.backend.routes.mood import router as mood_router


def get_app(config) -> FastAPI:
    @asynccontextmanager
    async def lifespan(a: FastAPI):
        if not config.AUTH_TOKEN_SECRET_KEY:
            raise Exception(
                "Please set AUTH_TOKEN_SECRET_KEY environment variable"
            )

        init_db(config.SQLITE_DB_PATH)
        yield

    app = FastAPI(
        title=config.APP_TITLE,
        description=config.APP_DESCRIPTION,
        lifespan=lifespan,
        root_path=config.ROOT_PATH,
    )

    @app.exception_handler(BaseApplicationException)
    async def base_application_exception_handler(
        request: Request, exc: BaseApplicationException
    ):
        raise HTTPException(
            status_code=exc.http_status_code, detail=exc.message
        )

    app.include_router(auth_router, tags=["Auth"], prefix="/auth")
    app.include_router(mood_router, tags=["Mood"], prefix="/mood")

    return app
