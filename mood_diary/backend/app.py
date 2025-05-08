import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
from starlette.responses import JSONResponse

from mood_diary.backend.config import CsrfProtectSettings, config
from mood_diary.backend.database.db import init_db
from mood_diary.backend.exceptions.base import BaseApplicationException
from mood_diary.backend.routes.auth import router as auth_router
from mood_diary.backend.routes.mood import router as mood_router
from mood_diary.backend.config import config

logging.basicConfig(
    level=config.LOGGING_LEVEL,
    format=config.LOGGING_FORMAT,
    datefmt=config.LOGGING_DATE_FORMAT,
)

logger = logging.getLogger(__name__)

def get_app(app_config) -> FastAPI:
	@asynccontextmanager
	async def lifespan(a: FastAPI):
		if not app_config.AUTH_TOKEN_SECRET_KEY:
			raise Exception(
				"Please set AUTH_TOKEN_SECRET_KEY environment variable"
			)

		if not app_config.CSRF_SECRET_KEY:
			raise Exception(
				"Please set CSRF_SECRET_KEY environment variable"
			)

		init_db(app_config.SQLITE_DB_PATH)
		yield

	app = FastAPI(
		title=app_config.APP_TITLE,
		description=app_config.APP_DESCRIPTION,
		lifespan=lifespan,
		root_path=app_config.ROOT_PATH,
	)

	@app.exception_handler(BaseApplicationException)
	async def base_application_exception_handler(
			request: Request, exc: BaseApplicationException
	):
		raise HTTPException(
			status_code=exc.http_status_code, detail=exc.message
		)

	@app.exception_handler(CsrfProtectError)
	def csrf_protect_exception_handler(
			request: Request, exc: CsrfProtectError
	):
		return JSONResponse(
			status_code=exc.status_code,
			content={"detail": exc.message}
		)

	app.include_router(auth_router, tags=["Auth"], prefix="/auth")
	app.include_router(mood_router, tags=["Mood"], prefix="/mood")

	return app
