"""Structured logging setup for the coder package.

Configures structlog with rich console rendering for human-readable
timestamped log output to stderr. Optionally writes to a log file.

All modules should use ``get_logger(__name__)`` to obtain a bound logger.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from coder.config import CoderConfig


def setup_logging(config: CoderConfig) -> None:
    """Configure structlog with rich console rendering.

    Sets up structured logging with:
    - Rich console output to stderr
    - Configurable log level (default DEBUG)
    - Optional file sink
    - Context fields: timestamp, level, module, event

    Args:
        config: CoderConfig instance with log_level and log_file settings.
    """
    log_level = getattr(
        logging, config.log_level.upper(), logging.DEBUG
    )

    # Configure the shared processors for all output
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog to use stdlib logging as the backend
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    # Build the formatter with rich console rendering
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=shared_processors,
    )

    # Set up the root logger
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates on repeated calls
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # Console handler → stderr
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if config.log_file:
        try:
            file_handler = logging.FileHandler(
                config.log_file, mode="a"
            )
            file_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(
                    colors=False
                ),
                foreign_pre_chain=shared_processors,
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            # Log file not writable — warn and continue console-only
            root_logger.warning(
                "Unable to open log file '%s' for writing. "
                "Continuing with console-only logging.",
                config.log_file,
            )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger with the given module name.

    The returned logger includes the module name as context, which
    appears in all log events from this logger.

    Args:
        name: Module name (typically ``__name__``).

    Returns:
        A bound structlog logger instance.
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
