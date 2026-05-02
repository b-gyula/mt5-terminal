from typing import Final
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from apscheduler.schedulers.background import BackgroundScheduler
import yaml
import json
from app.routers import trading, auth, account, positions, symbols, history, terminal
from app.dependencies.auth import verify_api_key
from app.db.database import init_db
from app.utils.exceptions import MT5BaseException
from app.utils.logger import logger_instance
from app.utils import config
from app.utils.config import env, DEV_STATE
from app.utils.trailing import trailing_stop_handler
from app.utils.constants import CHARSET_UTF8
from app.utils.helpers import raw_body

logger = logger_instance.get_logger()
scheduler = BackgroundScheduler()

API_PREFIX: Final = ""  # "/api/v1"

CHARSET_LATIN: Final = "latin-1"
HDR_CONTENT_TYPE: Final ="content-type"
MEDIA_TYPE_JSON: Final = "application/json"
MEDIA_TYPE_TEXT: Final = "text/plain"
CHARSET: Final = "charset"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Initializing Database...")
    init_db()

    # Secure API Key Generation
    if env.API_KEY_SEED:
        logger.info(f"API Key successfully generated from seed: {config.settings.api_key}")
    else:
        logger.warning("No API_KEY_SEED found! Authentication will be disabled.")

    # Start scheduled tasks
    if env.TS_REFRESH_PERIOD > 0:
        logger.info("Starting Background Scheduler...")
        scheduler.add_job(trailing_stop_handler, "interval", seconds=env.TS_REFRESH_PERIOD)
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
        title=config.API_NAME,
        description=config.API_DESCRIPTION,
        version=config.API_VERSION,
        debug=config.env.ENV_STATE == DEV_STATE,
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
        """
        Middleware to handle text/plain POST requests as YAML.
        
        - Detects requests with Content-Type: text/plain
        - Parses the body as YAML
        - Converts to JSON for FastAPI's body parser
        - Stores original body in request.state.raw_body for logging
        """
        if request.method in ("POST", "PUT", "PATCH") and \
           MEDIA_TYPE_TEXT in request.headers.get(HDR_CONTENT_TYPE, MEDIA_TYPE_TEXT):
            body = await request.body()
            if body:
                try:
                    # Decode the original body
                    # Store original body in request state for access in routes
                    request.state.raw_body = body.decode(CHARSET_UTF8)

                    # Parse YAML and convert to JSON for FastAPI
                    data = yaml.safe_load(body)
                    request._body = json.dumps(data).encode(CHARSET_UTF8)
                    
                    # Replace content-type header so FastAPI treats body as JSON
                    hdrs = request.headers.mutablecopy()
                    hdrs[HDR_CONTENT_TYPE] = f"{MEDIA_TYPE_JSON}; charset={CHARSET_UTF8}"
                    hdrs['content-length'] = str(len(request._body))
                    request.scope["headers"] = hdrs.raw

                except yaml.YAMLError as e:
                    logger.warning(f"Unable to parse request:\n'{body.decode(CHARSET_LATIN)}'\n" +
                                   f" as YAML: {e}")

        return await call_next(request)

    async def send_error_mail(r: Request, ex: Exception):
        from app.utils import email
        if r.url.path in ('/trade/order'):
            email.send_order_mail(await raw_body(r), None, ex)

    @app.exception_handler(RequestValidationError)
    async def valueError_exception_handler(request: Request, ex: RequestValidationError):
        await send_error_mail(request, ex)
        from fastapi.encoders import jsonable_encoder
        return JSONResponse(jsonable_encoder(ex.errors(), exclude=('ctx',)), 422)
        # return JSONResponse({'error':jsonable_encoder(exc.errors())}, 422)

    @app.exception_handler(MT5BaseException)
    async def mt5_exception_handler(request: Request, ex: MT5BaseException):
        await send_error_mail(request, ex)
        # Log the exception with full stack trace
        logger.error(
            f"{ex.__class__.__name__}: {ex.code}: {ex.message} in {request.url.path}"
            # ,exc_info=True  # This includes the full stack trace
        )
        return JSONResponse({"error": ex.message, "code": ex.code}, 400)

    # Health Check (Internal/System)
    @app.get("/health", tags=["System"])
    def health_check():
        return {"status": "ok", "version": config.API_VERSION}

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
