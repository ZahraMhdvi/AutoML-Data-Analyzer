import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.core.db import ROOT_DIR, init_db
from api.routes import auth as auth_routes
from api.routes import health as health_routes
from api.routes import projects as project_routes
from ml_engine.ai.llm_target_service import config_status
from ml_engine.errors import AppError


logger = logging.getLogger("guidml")

FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


@asynccontextmanager
async def lifespan(_app):
    init_db()
    status = config_status()
    if status["configured"]:
        logger.info("LLM service configured (models: %s)", ", ".join(status["models"]))
    else:
        logger.warning("LLM service not configured: %s. Pseudo-targets will use the statistical "
                       "generator and be labelled as such.", ", ".join(status["problems"]))
    yield


app = FastAPI(title="GuidML - AutoML Data Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.to_dict()})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request, exc):
    return JSONResponse(status_code=422, content={"detail": {
        "code": "VALIDATION_ERROR", "message": "The request is incomplete or invalid.",
        "params": {"fields": [".".join(str(p) for p in e.get("loc", [])) for e in exc.errors()]}}})


@app.exception_handler(HTTPException)
async def http_error_handler(_request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail),
                                                               "params": {}}
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(Exception)
async def unexpected_error_handler(_request, exc):
    logger.exception("Unexpected error")
    return JSONResponse(status_code=500, content={"detail": {
        "code": "INTERNAL_ERROR", "message": "Unexpected server error.", "params": {}}})


app.include_router(auth_routes.router)
app.include_router(project_routes.router)
app.include_router(health_routes.router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
