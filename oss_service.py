from __future__ import annotations

from datetime import datetime, timedelta, timezone
import heapq
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import oss2

from app_defs import format_datetime
from oss_config import OssConfig
from oss_models import BucketOption, ObjectPage, OssObject, UploadOptions


MAX_LIST_KEYS = 1000
CONNECT_TIMEOUT_SECONDS = 15
BYTES_PER_MB = 1024 * 1024
KEY_SEPARATORS = (".aliyuncs.com/", ".aliyuncs.com")
META_CREATED_AT = "x-oss-meta-created-at"
META_EXPIRES_AT = "x-oss-meta-expires-at"
META_LINK_MODE = "x-oss-meta-link-mode"
PUBLIC_LINK_MODE = "public"
SIGNED_LINK_MODE = "signed"
NEVER_EXPIRES = "never"


class OssService:
    def __init__(self, config: OssConfig) -> None:
        self._auth = oss2.Auth(config.access_key_id, config.access_key_secret)
        self._config = config
        self._bucket_name = config.bucket
        self._endpoint = self._normalize_endpoint(config.endpoint)
        self._upload_endpoint = self._normalize_endpoint(config.upload_endpoint or config.endpoint)
        self._bucket_endpoints: dict[str, str] = {config.bucket: self._endpoint}
        self._bucket = self._build_bucket(config.bucket, self._endpoint)
        self._upload_bucket = self._build_bucket(config.bucket, self._upload_endpoint)

    @property
    def bucket_name(self) -> str:
        return self._bucket_name

    @property
    def page_size(self) -> int:
        return self._config.page_size

    @property
    def multipart_threads(self) -> int:
        return self._config.multipart_threads

    def list_buckets(self) -> list[BucketOption]:
        service = oss2.Service(self._auth, self._config.endpoint)
        bucket_infos = service.list_buckets().buckets
        options: list[BucketOption] = []
        for bucket in bucket_infos:
            self._bucket_endpoints[bucket.name] = bucket.extranet_endpoint
            options.append(BucketOption(bucket.name, bucket.extranet_endpoint))
        return options

    def use_bucket(self, bucket_name: str) -> None:
        clean_name = bucket_name.strip()
        if not clean_name:
            raise ValueError("Bucket 不能为空")
        endpoint = self._bucket_endpoints.get(clean_name, self._endpoint)
        self._bucket_name = clean_name
        self._endpoint = endpoint
        self._upload_endpoint = self._normalize_endpoint(self._config.upload_endpoint or endpoint)
        self._bucket = self._build_bucket(clean_name, endpoint)
        self._upload_bucket = self._build_bucket(clean_name, self._upload_endpoint)

    def _build_bucket(self, bucket_name: str, endpoint: str):
        return oss2.Bucket(
            self._auth,
            endpoint,
            bucket_name,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )

    def list_objects(self, prefix: str) -> list[OssObject]:
        page = self.list_objects_page(prefix, "", MAX_LIST_KEYS)
        return page.objects

    def list_objects_page(self, prefix: str, marker: str, page_size: int) -> ObjectPage:
        clean_prefix = self.prefix_from_input(prefix)
        page_no = self._page_no_from_marker(marker)
        keep_count = page_size * page_no
        latest, total_count = self._latest_object_summaries(clean_prefix, keep_count)
        latest.sort(key=lambda item: item[0], reverse=True)
        start = (page_no - 1) * page_size
        page_items = [self._to_object(item[2]) for item in latest[start:keep_count]]
        next_marker = str(page_no + 1) if total_count > keep_count else ""
        return ObjectPage(page_items, next_marker, total_count)

    def _latest_object_summaries(self, prefix: str, keep_count: int) -> tuple[list[tuple[int, int, object]], int]:
        heap: list[tuple[int, int, object]] = []
        total_count = 0
        for index, obj in enumerate(oss2.ObjectIterator(self._bucket, prefix=prefix, max_keys=MAX_LIST_KEYS)):
            total_count += 1
            item = (int(obj.last_modified), index, obj)
            if len(heap) < keep_count:
                heapq.heappush(heap, item)
                continue
            if item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)
        return heap, total_count

    def upload_file(
        self,
        local_path: Path,
        object_key: str,
        options: UploadOptions,
        progress_callback=None,
    ) -> str:
        self._require_file(local_path)
        clean_key = self._normalize_key(object_key)
        total_size = local_path.stat().st_size
        headers = self._upload_headers(options)
        self._emit_progress(progress_callback, 0, total_size)
        if self._should_multipart(total_size):
            self._upload_resumable(local_path, clean_key, headers, progress_callback)
        else:
            self._upload_single(local_path, clean_key, headers, progress_callback)
        self._emit_progress(progress_callback, total_size, total_size)
        return self.public_url(clean_key)

    def _upload_single(self, local_path: Path, object_key: str, headers: dict[str, str], progress_callback) -> None:
        self._upload_bucket.put_object_from_file(
            object_key,
            str(local_path),
            headers=headers,
            progress_callback=progress_callback,
        )

    def _upload_resumable(
        self,
        local_path: Path,
        object_key: str,
        headers: dict[str, str],
        progress_callback,
    ) -> None:
        oss2.resumable_upload(
            self._upload_bucket,
            object_key,
            str(local_path),
            headers=headers,
            multipart_threshold=self._mb_to_bytes(self._config.multipart_threshold_mb),
            part_size=self._mb_to_bytes(self._config.multipart_part_size_mb),
            num_threads=self._config.multipart_threads,
            progress_callback=progress_callback,
        )

    def _should_multipart(self, total_size: int) -> bool:
        return total_size >= self._mb_to_bytes(self._config.multipart_threshold_mb)

    def delete_file(self, object_key: str) -> None:
        self._bucket.delete_object(self._normalize_key(object_key))

    def download_file(self, object_key: str, target_path: Path) -> None:
        clean_key = self._normalize_key(object_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        self._bucket.get_object_to_file(clean_key, str(target_path))

    def public_url(self, object_key: str) -> str:
        clean_key = self._normalize_key(object_key)
        encoded_key = quote(clean_key, safe="/")
        return f"https://{self._bucket_name}.{self._endpoint}/{encoded_key}"

    def signed_url(self, object_key: str, expire_seconds: int | None = None) -> str:
        return self._bucket.sign_url(
            "GET",
            self._normalize_key(object_key),
            expire_seconds or self._config.signed_url_expire_seconds,
            slash_safe=True,
        )

    def upload_file_url(self, local_path: Path, options: UploadOptions, progress_callback=None) -> str:
        clean_key = self._normalize_key(options.object_key)
        self.upload_file(local_path, clean_key, options, progress_callback)
        if not options.use_signed_url:
            return self.public_url(clean_key)
        return self.signed_url(clean_key, options.expire_days * 24 * 60 * 60)

    def count_objects(self, prefix: str) -> int:
        count = 0
        for _ in oss2.ObjectIterator(self._bucket, prefix=prefix, max_keys=MAX_LIST_KEYS):
            count += 1
        return count

    def key_from_url(self, url: str) -> str:
        raw_value = url.strip()
        parsed = urlparse(raw_value)
        if parsed.path and parsed.path != "/":
            return self._normalize_key(unquote(parsed.path.lstrip("/")))

        for separator in KEY_SEPARATORS:
            if separator in raw_value:
                return self._normalize_key(unquote(raw_value.split(separator, 1)[1]))

        raise ValueError("无法从链接解析 OSS 文件路径")

    def prefix_from_input(self, value: str) -> str:
        raw_value = value.strip()
        if not raw_value:
            return ""
        parsed = urlparse(raw_value)
        if "aliyuncs.com" in raw_value and parsed.path in ("", "/"):
            return ""
        if "aliyuncs.com" in raw_value:
            return self.key_from_url(raw_value)
        return raw_value.replace("\\", "/").lstrip("/")

    @staticmethod
    def _page_no_from_marker(marker: str) -> int:
        if not marker:
            return 1
        value = int(marker)
        if value <= 0:
            raise ValueError("页码标记必须大于 0")
        return value

    def _to_object(self, obj) -> OssObject:
        headers = self._object_headers(obj.key)
        return OssObject(
            key=obj.key,
            size=int(obj.size),
            created_at=self._display_created_at(headers, obj.last_modified),
            last_modified=format_datetime(obj.last_modified),
            last_modified_ts=int(obj.last_modified),
            expires_at=self._display_expires_at(headers),
            storage_class=str(getattr(obj, "storage_class", "")),
            url=self.public_url(obj.key),
        )

    def _upload_headers(self, options: UploadOptions) -> dict[str, str]:
        now = datetime.now(timezone.utc)
        expires_at = NEVER_EXPIRES
        link_mode = PUBLIC_LINK_MODE
        if options.use_signed_url:
            expires_at = (now + timedelta(days=options.expire_days)).isoformat()
            link_mode = SIGNED_LINK_MODE
        return {
            META_CREATED_AT: now.isoformat(),
            META_EXPIRES_AT: expires_at,
            META_LINK_MODE: link_mode,
        }

    def _object_headers(self, object_key: str) -> dict[str, str]:
        return {key.lower(): value for key, value in self._bucket.head_object(object_key).headers.items()}

    def _display_created_at(self, headers: dict[str, str], last_modified: int) -> str:
        return format_datetime(headers.get(META_CREATED_AT) or last_modified)

    def _display_expires_at(self, headers: dict[str, str]) -> str:
        return format_datetime(headers.get(META_EXPIRES_AT) or NEVER_EXPIRES)

    @staticmethod
    def _mb_to_bytes(value: int) -> int:
        return value * BYTES_PER_MB

    @staticmethod
    def _emit_progress(callback, consumed: int, total: int) -> None:
        if callback:
            callback(consumed, total)

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        parsed = urlparse(endpoint)
        return parsed.netloc or endpoint.replace("https://", "").replace("http://", "")

    @staticmethod
    def _require_file(local_path: Path) -> None:
        if not local_path.is_file():
            raise FileNotFoundError(f"本地文件不存在: {local_path}")

    @staticmethod
    def _normalize_key(object_key: str) -> str:
        clean_key = object_key.strip().replace("\\", "/").lstrip("/")
        if not clean_key:
            raise ValueError("OSS 文件路径不能为空")
        return clean_key
