"""
@module Logger
@description Application-wide structured logging utility.
             Only outputs debug logs when DEBUG=true in environment.
"""
import os
import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("civicpulse")
_DEBUG = os.getenv("DEBUG", "false").lower() == "true"

class Logger:
    @staticmethod
    def info(msg: str) -> None:
        """@description Logs an info message. @param msg: str @returns None"""
        _logger.info(msg)

    @staticmethod
    def error(msg: str) -> None:
        """@description Logs an error message. @param msg: str @returns None"""
        _logger.error(msg)

    @staticmethod
    def debug(msg: str) -> None:
        """@description Logs a debug message only when DEBUG=true. @param msg: str @returns None"""
        if _DEBUG:
            _logger.debug(msg)

    @staticmethod
    def warn(msg: str) -> None:
        """@description Logs a warning message. @param msg: str @returns None"""
        _logger.warning(msg)
