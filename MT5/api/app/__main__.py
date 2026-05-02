import uvicorn
import sys
from app.utils import config
from app.utils.config import env, DEV_STATE
from app.utils.logger import logger_instance
from typing import Final

logger = logger_instance.get_logger()

LOG_FILE: Final = 'logging.yml'

def main():
    logger.info(
        f"Starting {config.API_NAME} {config.API_VERSION} on {env.HOST}:{env.PORT} python:{sys.version}"
    )
    uvicorn.run(
        "app.main:app",
        host=env.HOST,
        port=env.PORT,
        reload=env.ENV_STATE == DEV_STATE,
        log_level=env.LOG_LEVEL.lower(),
#        log_config=LOG_FILE if os.path.isfile(LOG_FILE) else uvicorn.config.LOGGING_CONFIG,
    )

if __name__ == "__main__":
    main()