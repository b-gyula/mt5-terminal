import logging
import sys
from app.utils.config import env, settings

class LoggerInstance:
    def __init__(self, name="app"):
        log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
        log_file = "api.log"

        self.logger = logging.getLogger(name)
        self.logger.setLevel(
            getattr(logging, env.LOG_LEVEL.upper(), logging.INFO)
        )

        if not self.logger.handlers:
            formatter = logging.Formatter(log_format)

            # Console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            # File handler
            log_dir = settings.logs_dir
            fh = logging.FileHandler(log_dir / log_file)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def get_logger(self):
        return self.logger

logger_instance = LoggerInstance()
