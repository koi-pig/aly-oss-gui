from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


CONFIG_FILE = "config.local.json"
DEFAULT_CONFIG = {
    "access_key_id": "",
    "access_key_secret": "",
    "bucket": "",
    "endpoint": "http://oss-cn-hangzhou.aliyuncs.com",
    "upload_endpoint": "",
    "view_endpoint": "https://%s.oss-cn-hangzhou.aliyuncs.com/%s",
    "signed_url_expire_seconds": 315360000,
    "page_size": 10,
    "multipart_threshold_mb": 10,
    "multipart_part_size_mb": 16,
    "multipart_threads": 32,
}


@dataclass(frozen=True)
class OssConfig:
    access_key_id: str
    access_key_secret: str
    bucket: str
    endpoint: str
    upload_endpoint: str
    view_endpoint: str
    signed_url_expire_seconds: int
    page_size: int
    multipart_threshold_mb: int
    multipart_part_size_mb: int
    multipart_threads: int


def load_config(base_dir: Path) -> OssConfig:
    config_path = base_dir / CONFIG_FILE
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    required = (
        "access_key_id",
        "access_key_secret",
        "bucket",
        "endpoint",
        "view_endpoint",
        "signed_url_expire_seconds",
    )
    missing = [key for key in required if not data.get(key)]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"配置文件缺少字段: {joined}")

    return OssConfig(
        access_key_id=str(data["access_key_id"]),
        access_key_secret=str(data["access_key_secret"]),
        bucket=str(data["bucket"]),
        endpoint=str(data["endpoint"]),
        upload_endpoint=str(data.get("upload_endpoint", "")),
        view_endpoint=str(data["view_endpoint"]),
        signed_url_expire_seconds=int(data["signed_url_expire_seconds"]),
        page_size=int(data.get("page_size", 10)),
        multipart_threshold_mb=int(data.get("multipart_threshold_mb", 10)),
        multipart_part_size_mb=int(data.get("multipart_part_size_mb", 16)),
        multipart_threads=int(data.get("multipart_threads", 32)),
    )


def config_path(base_dir: Path) -> Path:
    return base_dir / CONFIG_FILE


def read_config_data(base_dir: Path) -> dict[str, object]:
    path = config_path(base_dir)
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return DEFAULT_CONFIG | data


def save_config_data(base_dir: Path, data: dict[str, object]) -> Path:
    path = config_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path
