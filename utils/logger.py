import os
import logging
from dotenv import load_dotenv

load_dotenv()

_configured = False

def _configure_logging():
    global _configured
    if _configured:
        return

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "math_mentor.log")

    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    level = logging.DEBUG if debug_mode else logging.INFO

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on reload
    if not root.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
        root.addHandler(ch)

        # File handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
        root.addHandler(fh)

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "filelock", "transformers", "sentence_transformers"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


_configure_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger. Call at module level:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)