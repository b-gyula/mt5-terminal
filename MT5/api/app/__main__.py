import uvicorn
import sys
from app.utils.config import settings, DEV_STATE
from app.utils.logger import logger_instance
from typing import Final

logger = logger_instance.get_logger()

LOG_FILE: Final = 'logging.yml'

def main():
    logger.info(
        f"Starting {settings.API_NAME} {settings.API_VERSION} on {settings.env.HOST}:{settings.env.PORT} python:{sys.version}"
    )
    uvicorn.run(
        "app.main:app",
        host=settings.env.HOST,
        port=settings.env.PORT,
        reload=settings.env.ENV_STATE == DEV_STATE,
        log_level=settings.env.LOG_LEVEL.lower(),
#        log_config=LOG_FILE if os.path.isfile(LOG_FILE) else uvicorn.config.LOGGING_CONFIG,
    )

if __name__ == "__main__":
    main()