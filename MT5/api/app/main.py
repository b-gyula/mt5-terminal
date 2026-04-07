import sys
from typing import Final
from app.utils.config import settings
# import logging
from contextlib import asynccontextmanager

try:
    import MetaTrader5 as mt5
except ImportError:
    print("CRITICAL ERROR: Required MetaTrader5 library is not installed")
    sys.exit(1)

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yaml
import json
from app.routers import trading, auth, account, positions, symbols, history, terminal
from app.dependencies.auth import verify_api_key
from app.db.database import init_db
from app.utils.exceptions import MT5BaseException
from app.utils.logger import logger_instance
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.trailing import trailing_stop_handler
from prometheus_fastapi_instrumentator import Instrumentator

logger = logger_instance.get_logger()
scheduler = BackgroundScheduler()

API_PREFIX: Final = ""  # "/api/v1"

CHARSET_UTF8 = "utf-8"
CHARSET_LATIN = "latin-1"
HDR_CONTENT_TYPE="content-type"
MEDIA_TYPE_JSON = "application/json"
MEDIA_TYPE_TEXT = "text/plain"
CHARSET = "charset"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Initializing Database...")
    init_db()

    # Secure API Key Generation
    if settings.env.API_KEY_SEED:
        logger.info(f"API Key successfully generated from seed: {settings.api_key}")
    else:
        logger.warning("No API_KEY_SEED found! Authentication will be disabled.")

    # Start scheduled tasks
    if settings.env.TS_REFRESH_PERIOD > 0:
        logger.info("Starting Background Scheduler...")
        scheduler.add_job(trailing_stop_handler, "interval", seconds=settings.env.TS_REFRESH_PERIOD)
        scheduler.start()
    else:
        logger.info("Trailing Stop is disabled. Set env TS_REFRESH_PERIOD > 0 to enable it.")

    yield

    # Shutdown event
    if scheduler.running:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.env.API_NAME,
        description=settings.env.API_DESCRIPTION,
        version=settings.env.API_VERSION,
        debug=settings.env.API_DEBUG_MODE,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    @app.middleware("http")
    async def yamlDeserializer(request: Request, call_next):
        #content_type, params = parse_options_header(  )
        
        if request.method in ("POST", "PUT", "PATCH") and \
           MEDIA_TYPE_TEXT in request.headers.get(HDR_CONTENT_TYPE, MEDIA_TYPE_TEXT):
            body = await request.body()
            if body:
                try:
                    # Replace the content-type header in the ASGI scope so
                    # FastAPI's body parser treats the rewritten body as JSON.
            
                    # Get charset (default to utf-8 if not specified)
                    #charset = params.get(b"charset", b"utf-8").decode(CHARSET_LATIN)
                    data = yaml.safe_load(body)
                    request._body = json.dumps(data).encode(CHARSET_UTF8)
                    hdrs = request.headers.mutablecopy()
                    hdrs[HDR_CONTENT_TYPE] = "application/json; charset=utf-8"
                    hdrs['content-length'] = str(len(request._body)) #.encode(CHARSET_UTF8)
                    request.scope["headers"] = hdrs.raw

                except yaml.YAMLError as e:
                    logger.warning(f"Unable to parse request:\n'{body.decode(CHARSET_LATIN)}'\n as YAML: {e}")

        return await call_next(request)

    @app.exception_handler(MT5BaseException)
    async def mt5_exception_handler(request: Request, exc: MT5BaseException):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message, "code": exc.code},
        )

    # Health Check (Internal/System)
    @app.get("/health", tags=["System"])
    def health_check():
        return {"status": "ok", "version": settings.env.API_VERSION}

    # Auth routes (Unprotected)
    app.include_router(
        auth.router, prefix=API_PREFIX
    )

    # Protected routes
    app.include_router(
        trading.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )
    app.include_router(
        account.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )
    app.include_router(
        positions.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )
    app.include_router(
        symbols.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )
    app.include_router(
        history.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )
    app.include_router(
        terminal.router, prefix=API_PREFIX, dependencies=[Depends(verify_api_key)]
    )

    @app.api_route("/", methods=["GET", "HEAD"], tags=["System"])
    def read_root():
        return {"message": "Welcome to MetaTrader 5 API", "docs": "/docs"}

    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
