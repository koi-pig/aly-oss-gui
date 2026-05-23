from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QTableWidgetItem

from app_defs import DEFAULT_EXPIRE_DAYS, UploadRequest, app_base_dir, format_duration, format_size, open_file
from batch_upload import BatchUploadResult, BatchUploader
from config_dialog import ConfigDialog
from oss_config import load_config
from oss_models import ObjectPage, OssObject, UploadOptions
from oss_service import OssService


class DataMixin:
    @Slot()
    def upload(self) -> None:
        requests = self._build_upload_requests()
        if len(requests) == 1:
            self._upload_single_request(requests[0])
            return
        self._upload_batch_requests(requests)

    def _upload_single_request(self, request: UploadRequest) -> None:
        self._start_upload_stats(request.local_path)
        self._write_log(f"准备上传: {request.local_path} -> {request.object_key}")
        self._write_log(f"文件大小: {format_size(self._upload_total_size)}")
        options = self._upload_options(request)
        self._run_task("上传文件", lambda cb: self._service.upload_file_url(
            request.local_path,
            options,
            cb,
        ), self._show_upload_url, True)

    def _upload_batch_requests(self, requests: list[UploadRequest]) -> None:
        self._start_batch_upload_stats(requests)
        self._write_log(f"准备批量上传: {len(requests)} 个文件，总大小 {format_size(self._upload_total_size)}")
        uploader = BatchUploader(self._service, min(self._service.multipart_threads, 8))
        self._run_task("批量上传", lambda cb: uploader.upload(requests, cb), self._show_batch_upload_result, True)

    @Slot()
    def replace_by_url(self) -> None:
        request = self._build_replace_request()
        self._start_upload_stats(request.local_path)
        self._write_log(f"准备替换: {request.local_path} -> {request.object_key}")
        self._write_log(f"文件大小: {format_size(self._upload_total_size)}")
        options = self._upload_options(request)
        self._run_task("替换文件", lambda cb: self._service.upload_file_url(
            request.local_path,
            options,
            cb,
        ), self._show_upload_url, True)


    @Slot()
    def overwrite_selected(self) -> None:
        key = self._selected_key()
        filename, _ = QFileDialog.getOpenFileName(self, "选择覆盖文件")
        if not filename:
            return
        local_path = Path(filename)
        self._start_upload_stats(local_path)
        self._write_log(f"文件大小: {format_size(self._upload_total_size)}")
        options = UploadOptions(key, self._use_signed_url(), self._expire_days_value())
        self._run_task("覆盖文件", lambda cb: self._service.upload_file_url(
            local_path,
            options,
            cb,
        ), self._show_upload_url, True)


    @Slot()
    def copy_last_upload_url(self) -> None:
        url = self._last_upload_url.text().strip()
        if not url:
            raise ValueError("还没有上传完成的链接")
        self._copy_text(url)

    @Slot()
    def count_total(self) -> None:
        prefix = self._current_prefix or self._prefix.text().strip()
        clean = self._service.prefix_from_input(prefix)
        self._write_log(f"开始统计总数，前缀: {clean or '(全部)'}")
        self._run_task("统计总数", lambda _: self._service.count_objects(clean), self._show_total_count)

    @Slot()
    def open_config(self) -> None:
        open_file(app_base_dir() / "config.local.json")

    @Slot()
    def edit_oss_config(self) -> None:
        base_dir = app_base_dir()
        dialog = ConfigDialog(base_dir, self)
        if dialog.exec() != QDialog.Accepted:
            return
        config = load_config(base_dir)
        self._service = OssService(config)
        self._page_size.setText(str(config.page_size))
        self._reset_bucket(config.bucket)
        self._write_log(f"OSS 配置已保存并重新加载。当前 Bucket: {config.bucket}")

    def _show_upload_url(self, url: str) -> None:
        self._last_upload_url.setText(url)
        QApplication.clipboard().setText(url)
        self._write_log(f"上传完成，链接已复制: {url}")
        self._write_upload_stats()

    def _show_batch_upload_result(self, result: BatchUploadResult) -> None:
        first_url = result.urls[0] if result.urls else ""
        self._last_upload_url.setText(first_url)
        if first_url:
            QApplication.clipboard().setText(first_url)
        self._write_log(f"批量上传完成，共 {len(result.urls)} 个文件，第一条链接已复制: {first_url}")
        self._write_upload_stats()

    def _start_batch_upload_stats(self, requests: list[UploadRequest]) -> None:
        self._upload_started_at = time.perf_counter()
        self._last_progress_at = self._upload_started_at
        self._last_progress_bytes = 0
        self._upload_total_size = sum(item.local_path.stat().st_size for item in requests)

    def _start_upload_stats(self, local_path: Path) -> None:
        self._upload_started_at = time.perf_counter()
        self._last_progress_at = self._upload_started_at
        self._last_progress_bytes = 0
        self._upload_total_size = local_path.stat().st_size

    def _write_upload_stats(self) -> None:
        elapsed = max(time.perf_counter() - self._upload_started_at, 0.001)
        speed = int(self._upload_total_size / elapsed)
        self._write_log(
            f"上传统计: 大小 {format_size(self._upload_total_size)}，"
            f"用时 {format_duration(elapsed)}，平均速度 {format_size(speed)}/s"
        )


    def _reset_bucket(self, bucket_name: str) -> None:
        self._bucket.blockSignals(True)
        self._bucket.clear()
        self._bucket.addItem(bucket_name)
        self._bucket.blockSignals(False)

    def _show_total_count(self, total_count: int) -> None:
        text = f"总数 {total_count}，当前页 {len(self._page_markers)}"
        self._page_info.setText(text)
        self._write_log(text)

    def _page_size_value(self) -> int:
        value = int(self._page_size.text().strip() or self._service.page_size)
        if value <= 0:
            raise ValueError("每页数量必须大于 0")
        return value

    def _object_key_for_file(self, local_path: Path) -> str:
        current = self._object_key.text().strip().replace("\\", "/")
        if current.endswith("/"):
            return f"{current}{local_path.name}"
        prefix = current.rsplit("/", 1)[0] + "/" if "/" in current else ""
        return f"{prefix}{local_path.name}"

    def _build_upload_requests(self) -> list[UploadRequest]:
        files = self._selected_files or [Path(self._selected_file.text())]
        if len(files) == 1:
            return [self._build_upload_request()]
        prefix = self._upload_prefix()
        return [
            UploadRequest(path, f"{prefix}{path.name}", self._use_signed_url(), self._expire_days_value())
            for path in files
        ]

    def _upload_prefix(self) -> str:
        current = self._object_key.text().strip().replace("\\", "/")
        if not current:
            return ""
        return current if current.endswith("/") else current.rsplit("/", 1)[0] + "/" if "/" in current else ""

    def _build_upload_request(self) -> UploadRequest:
        return UploadRequest(
            Path(self._selected_file.text()),
            self._object_key.text(),
            self._use_signed_url(),
            self._expire_days_value(),
        )

    def _build_replace_request(self) -> UploadRequest:
        local_path = Path(self._selected_file.text())
        object_key = self._service.key_from_url(self._replace_url.text())
        return UploadRequest(
            local_path,
            object_key,
            self._use_signed_url(),
            self._expire_days_value(),
        )

    def _upload_options(self, request: UploadRequest) -> UploadOptions:
        return UploadOptions(request.object_key, request.use_signed_url, request.expire_days)

    def _use_signed_url(self) -> bool:
        return self._link_mode.currentText() == "签名链接"

    def _expire_days_value(self) -> int:
        value = int(self._expire_days.text().strip() or DEFAULT_EXPIRE_DAYS)
        if value <= 0:
            raise ValueError("过期天数必须大于 0")
        return value

    def _show_page(self, page: ObjectPage) -> None:
        self._next_marker = page.next_marker
        self._show_objects(page.objects)
        total = "未统计" if page.total_count < 0 else str(page.total_count)
        text = f"总数 {total}，本页 {len(page.objects)}，每页 {self._page_size_value()}，第 {len(self._page_markers)} 页"
        self._page_info.setText(text)
        self._write_log(text)

    def _show_objects(self, objects: list[OssObject]) -> None:
        self._table.setRowCount(0)
        for item in objects:
            self._append_object_row(item)
        self._write_log(f"列表已刷新，共 {len(objects)} 个文件")

    def _append_object_row(self, item: OssObject) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        values = (
            item.key,
            format_size(item.size),
            item.created_at,
            item.last_modified,
            item.expires_at,
            item.storage_class,
            item.url,
        )
        for column, value in enumerate(values):
            self._table.setItem(row, column, QTableWidgetItem(value))

    def _show_selected_link(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            self._link_detail.clear()
            return
        self._link_detail.setText(self._table.item(row, 6).text())

    def _selected_key(self) -> str:
        row = self._table.currentRow()
        if row < 0:
            raise ValueError("请先在列表中选择一个文件")
        return self._table.item(row, 0).text()
