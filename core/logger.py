import functools
import logging
import sys
import traceback
from typing import Any, Callable

# Configure standard logger to write strictly to stderr
logger = logging.getLogger("memorize")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that catches any unhandled exceptions in MCP tools or core functions,
    logs the detailed traceback to sys.stderr, and returns a clean error dictionary.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            func_name = func.__name__

            # Log detailed stack trace to stderr for developer debugging
            logger.error(f"Error in '{func_name}': {error_type} - {error_msg}")
            logger.debug(traceback.format_exc())

            # Return structured error object to AI client / caller
            return {
                "status": "error",
                "error_type": error_type,
                "message": error_msg,
                "function": func_name,
            }

    return wrapper
