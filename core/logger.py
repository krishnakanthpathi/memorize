import functools
import json
import logging
import sys
import time
import traceback
from typing import Any, Callable

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

# Configure standard logger to write strictly to stderr to preserve stdio JSON-RPC
logger = logging.getLogger("memorize")
logger.setLevel(logging.INFO)


class CompactTextFormatter(logging.Formatter):
    """Compact, single-line, subtle ANSI-formatted logger for CLI mode."""
    def format(self, record: logging.LogRecord) -> str:
        time_str = self.formatTime(record, "%H:%M:%S")
        level_str = record.levelname
        loc = f"{record.filename}:{record.lineno}"
        msg = record.getMessage()
        return f"\033[2;36m[{time_str}]\033[0m \033[2;33m[{level_str}]\033[0m \033[2;37m({loc})\033[0m \033[2m{msg}\033[0m"


def configure_cli_logging(level: str = "INFO"):
    """Configures subtle, compact single-line log formatting for CLI mode."""
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(CompactTextFormatter())
    logger.addHandler(handler)


if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    if HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(filename)s %(lineno)d %(message)s'
        )
    else:
        class CustomJSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_record = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "file": f"{record.filename}:{record.lineno}",
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    log_record["traceback"] = self.formatException(record.exc_info)
                return json.dumps(log_record)

        formatter = CustomJSONFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that catches any unhandled exceptions in MCP tools or core functions,
    logs detailed traceback to sys.stderr as structured JSON, and returns a clean error dictionary.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            func_name = func.__name__

            logger.error(f"Error in '{func_name}': {error_type} - {error_msg}")
            logger.debug(traceback.format_exc())

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
    Attaches 'execution_time_ms' if result is a dict.
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
