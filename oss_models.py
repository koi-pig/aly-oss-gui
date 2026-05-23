from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OssObject:
    key: str
    size: int
    created_at: str
    last_modified: str
    last_modified_ts: int
    expires_at: str
    storage_class: str
    url: str


@dataclass(frozen=True)
class BucketOption:
    name: str
    endpoint: str

    @property
    def label(self) -> str:
        return f"{self.name} -> {self.endpoint}"


@dataclass(frozen=True)
class ObjectPage:
    objects: list[OssObject]
    next_marker: str
    total_count: int


@dataclass(frozen=True)
class UploadOptions:
    object_key: str
    use_signed_url: bool
    expire_days: int
