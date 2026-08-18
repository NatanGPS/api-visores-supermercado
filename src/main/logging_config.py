import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging() -> None:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    # logs directory at project root
    logs_dir = os.path.join(base_dir, "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # errors folder already exists under src/errors; ensure file path
    errors_dir = os.path.join(base_dir, "errors")
    os.makedirs(errors_dir, exist_ok=True)

    api_log_path = os.path.abspath(os.path.join(logs_dir, "api_calls.log"))
    error_log_path = os.path.abspath(os.path.join(errors_dir, "errors.log"))

    # API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO)
    if not api_logger.handlers:
        api_handler = RotatingFileHandler(api_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        api_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        api_handler.setFormatter(api_formatter)
        api_logger.addHandler(api_handler)

    # Error logger
    err_logger = logging.getLogger("error")
    err_logger.setLevel(logging.ERROR)
    if not err_logger.handlers:
        err_handler = RotatingFileHandler(error_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        err_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(pathname)s:%(lineno)d - %(message)s")
        err_handler.setFormatter(err_formatter)
        err_logger.addHandler(err_handler)

    # Optionally configure root logger to also print to console
    root = logging.getLogger()
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(console)
