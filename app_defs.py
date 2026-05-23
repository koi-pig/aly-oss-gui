from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WINDOW_WIDTH = 1160
WINDOW_HEIGHT = 760
LOG_HEIGHT = 150
APP_VERSION = "2026-05-23.3"
DEFAULT_PAGE_SIZE = 10
DEFAULT_EXPIRE_DAYS = 365
EDIT_DIR_NAME = "aly_oss_gui_edit"
UPLOAD_TITLES = {"上传文件", "替换文件", "覆盖文件", "批量上传"}
COLUMNS = ("OSS 路径", "大小", "创建时间", "更新时间", "到期时间", "存储类型", "访问链接")
SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class UploadRequest:
    local_path: Path
    object_key: str
    use_signed_url: bool
    expire_days: int


def format_size(size: int) -> str:
    value = float(size)
    unit = SIZE_UNITS[0]
    for unit in SIZE_UNITS:
        if value < 1024 or unit == SIZE_UNITS[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)} B"
    return f"{value:.2f} {unit}"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f} sec"
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes} min {rest} sec"


def format_datetime(value: datetime | int | float | str | None) -> str:
    if value in (None, ""):
        return "未记录"
    if isinstance(value, datetime):
        return value.astimezone().strftime(DATE_TIME_FORMAT)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime(DATE_TIME_FORMAT)
    return _format_datetime_text(str(value))


def _format_datetime_text(value: str) -> str:
    if value == "never":
        return "永不过期"
    if value.isdigit():
        return datetime.fromtimestamp(int(value)).strftime(DATE_TIME_FORMAT)
    try:
        return datetime.fromisoformat(value).astimezone().strftime(DATE_TIME_FORMAT)
    except ValueError:
        return value


def open_file(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent
