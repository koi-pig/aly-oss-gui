from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock

from app_defs import UploadRequest
from oss_service import OssService, UploadOptions


@dataclass(frozen=True)
class BatchUploadResult:
    urls: list[str]
    total_size: int


class BatchUploader:
    def __init__(self, service: OssService, max_workers: int) -> None:
        self._service = service
        self._max_workers = max(1, max_workers)
        self._lock = Lock()
        self._done_by_key: dict[int, int] = {}

    def upload(self, requests: list[UploadRequest], progress_callback=None) -> BatchUploadResult:
        total_size = sum(item.local_path.stat().st_size for item in requests)
        self._emit(progress_callback, 0, total_size)
        urls: list[str] = []
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(requests))) as executor:
            futures = [
                executor.submit(self._upload_one, i, item, total_size, progress_callback)
                for i, item in enumerate(requests)
            ]
            for future in as_completed(futures):
                urls.append(future.result())
        self._emit(progress_callback, total_size, total_size)
        return BatchUploadResult(urls, total_size)

    def _upload_one(self, index: int, request: UploadRequest, total_size: int, progress_callback) -> str:
        options = UploadOptions(request.object_key, request.use_signed_url, request.expire_days)
        return self._service.upload_file_url(
            request.local_path,
            options,
            lambda consumed, _: self._on_file_progress(index, consumed, total_size, progress_callback),
        )

    def _on_file_progress(self, key: int, consumed: int, total_size: int, progress_callback) -> None:
        with self._lock:
            self._done_by_key[key] = int(consumed or 0)
            done = sum(self._done_by_key.values())
        self._emit(progress_callback, done, total_size)

    @staticmethod
    def _emit(callback, consumed: int, total: int) -> None:
        if callback:
            callback(consumed, total)
