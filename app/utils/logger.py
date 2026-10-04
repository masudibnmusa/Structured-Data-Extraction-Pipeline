import logging
import sys

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        logging.basicConfig(
            level=logging.INFO,
            stream=sys.stdout,
            format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        )
        _configured = True
    return logging.getLogger(name)