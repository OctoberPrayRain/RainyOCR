from enum import Enum


class TaskType(Enum):
    OCR = 1
    TRANSLATE = 2


class TaggedError(Exception):
    def __init__(self, message: str, *tags: str, **kwargs):
        super().__init__(message)
        self.tags = set(tags)
        self.extra = kwargs


def config_error(message: str, **kwargs) -> TaggedError:
    return TaggedError(message, "config", **kwargs)


def missing_key_error(key_name: str) -> TaggedError:
    return TaggedError(
        f"{key_name} not exist! Please check your configuration.",
        "config",
        "missing_key",
        key=key_name,
    )


def file_not_exist_error(file_name: str) -> TaggedError:
    return TaggedError(
        f"{file_name} not exist! Please check this file.", "file", file_name=file_name
    )


def network_error(status_code: int) -> TaggedError:
    return TaggedError(
        f"Network error: {status_code}", "network", status_code=status_code
    )


def baidu_api_error(message: str, error_code, task_type: TaskType) -> TaggedError:
    if task_type == TaskType.OCR:
        return TaggedError(
            f"Baidu OCR error: {error_code}, message: {message}",
            "Baidu OCR",
            error_code=error_code,
        )
    else:
        return TaggedError(
            f"Baidu Translate error: {error_code}, message: {message}",
            "Baidu Translate",
            error_code=error_code,
        )
