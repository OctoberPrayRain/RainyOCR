"""Application logging and crash diagnostics for RainyOCR."""

from __future__ import annotations

import faulthandler
import logging
import os
import platform
import signal
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import TextIO

from src.utils.paths import env_path, is_frozen_app, user_config_dir

LOGGER_NAME = "rainyocr"
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_CRASH_FILE: TextIO | None = None


def setup_logging() -> Path:
    """Configure application logging and native-crash stack dumps.

    Returns the directory containing ``rainyocr.log`` and
    ``rainyocr-crash.log`` so callers can surface it to users.
    """

    log_dir = rainyocr_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / "rainyocr.log"
    level = logging.DEBUG if os.getenv("RAINYOCR_DEBUG_LOG") == "1" else logging.INFO
    formatter = logging.Formatter(_LOG_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _install_exception_hooks()
    _enable_fault_handler(log_dir / "rainyocr-crash.log")

    logger = logging.getLogger(LOGGER_NAME)
    logger.info("RainyOCR logging initialized: %s", log_path)
    _log_runtime_summary(logger)
    return log_dir


def install_qt_message_handler() -> None:
    """Route Qt warnings/errors into the same log file."""

    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    logger = logging.getLogger(f"{LOGGER_NAME}.qt")

    def handle_qt_message(
        mode: QtMsgType,
        context: object,
        message: str,
    ) -> None:
        level = _qt_log_level(mode)
        location = _qt_context_location(context)
        if location:
            logger.log(level, "%s (%s)", message, location)
            return

        logger.log(level, "%s", message)

    qInstallMessageHandler(handle_qt_message)
    logger.info("Qt message handler installed")


def rainyocr_log_dir() -> Path:
    """Return the platform-appropriate RainyOCR log directory."""

    override = os.getenv("RAINYOCR_LOG_DIR")
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Logs" / "RainyOCR"
    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "RainyOCR" / "Logs"
        return home / "AppData" / "Local" / "RainyOCR" / "Logs"

    state_home = os.getenv("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "RainyOCR" / "logs"
    return home / ".local" / "state" / "RainyOCR" / "logs"


def _enable_fault_handler(crash_path: Path) -> None:
    global _CRASH_FILE

    if _CRASH_FILE is not None:
        _CRASH_FILE.close()

    _CRASH_FILE = crash_path.open("a", encoding="utf-8")
    _CRASH_FILE.write("\n--- RainyOCR crash diagnostics enabled ---\n")
    _CRASH_FILE.flush()
    faulthandler.enable(file=_CRASH_FILE, all_threads=True)
    logging.getLogger(LOGGER_NAME).info("faulthandler enabled: %s", crash_path)

    if hasattr(signal, "SIGUSR1"):
        try:
            faulthandler.register(signal.SIGUSR1, file=_CRASH_FILE, all_threads=True)
            logging.getLogger(LOGGER_NAME).info("SIGUSR1 traceback hook registered")
        except RuntimeError:
            logging.getLogger(LOGGER_NAME).debug("SIGUSR1 traceback hook unavailable")


def _install_exception_hooks() -> None:
    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        logging.getLogger(LOGGER_NAME).critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        if args.exc_value is None:
            logging.getLogger(LOGGER_NAME).critical(
                "Unhandled thread exception in %s without exception value",
                args.thread.name if args.thread else "unknown thread",
            )
            if threading.__excepthook__ is not None:
                threading.__excepthook__(args)
            return

        logging.getLogger(LOGGER_NAME).critical(
            "Unhandled thread exception in %s",
            args.thread.name if args.thread else "unknown thread",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        if threading.__excepthook__ is not None:
            threading.__excepthook__(args)

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception


def _log_runtime_summary(logger: logging.Logger) -> None:
    logger.info("Platform: %s", platform.platform())
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Executable: %s", sys.executable)
    logger.info("Working directory: %s", Path.cwd())
    logger.info("Arguments: %s", sys.argv)
    logger.info("Frozen app: %s", is_frozen_app())
    logger.info("User config directory: %s", user_config_dir())
    logger.info("Environment file path: %s", env_path())
    for variable in (
        "QT_QPA_PLATFORM",
        "QT_PLUGIN_PATH",
        "QT_DEBUG_PLUGINS",
        "AppleInterfaceStyle",
        "RAINYOCR_LOG_DIR",
        "RAINYOCR_DEBUG_LOG",
    ):
        logger.info("Environment %s=%s", variable, os.getenv(variable, ""))


def _qt_log_level(mode: object) -> int:
    name = getattr(mode, "name", "")
    if name == "QtDebugMsg":
        return logging.DEBUG
    if name == "QtInfoMsg":
        return logging.INFO
    if name == "QtWarningMsg":
        return logging.WARNING
    if name == "QtCriticalMsg":
        return logging.ERROR
    if name == "QtFatalMsg":
        return logging.CRITICAL
    return logging.WARNING


def _qt_context_location(context: object) -> str:
    file_path = getattr(context, "file", None)
    line = getattr(context, "line", 0)
    function = getattr(context, "function", None)
    parts = []
    if file_path:
        parts.append(str(file_path))
    if line:
        parts.append(str(line))
    if function:
        parts.append(str(function))
    return ":".join(parts)
