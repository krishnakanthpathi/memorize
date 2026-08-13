import functools
import logging
import sys
import time
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


def configure_cli_logging(level=logging.WARNING):
    """
    Configures logging verbosity for CLI interactive / execution modes.
    """
    logger.setLevel(level)
    for h in logger.handlers:
        h.setLevel(level)



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


def time_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that calculates and logs the execution duration of a function in milliseconds.
    If the return value is a dict, it attaches an 'execution_time_ms' key for timing stats.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(f"Execution time for '{func.__name__}': {elapsed_ms} ms")

        if isinstance(result, dict) and "execution_time_ms" not in result:
            result["execution_time_ms"] = elapsed_ms

        return result

    return wrapper
