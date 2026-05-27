"""Path helpers that work both from source and PyInstaller builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "RainyOCR"


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return project_root()


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def user_config_dir() -> Path:
    override = os.getenv("RAINYOCR_CONFIG_DIR")
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
        return home / "AppData" / "Roaming" / APP_NAME

    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME

    config_home = os.getenv("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / APP_NAME
    return home / ".config" / APP_NAME


def env_path() -> Path:
    if is_frozen_app():
        return user_config_dir() / ".env"
    return project_root() / ".env"


def candidate_env_paths() -> list[Path]:
    paths = [env_path()]
    for path in (Path.cwd() / ".env", resource_root() / ".env", project_root() / ".env"):
        if path not in paths:
            paths.append(path)
    return paths
