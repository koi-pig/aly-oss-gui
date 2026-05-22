from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QMessageBox

from app_defs import EDIT_DIR_NAME, UPLOAD_TITLES, format_size, open_file
from task_worker import TaskWorker


class TaskMixin:
    def _copy_text(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self._write_log(f"已复制: {text}")

    def _download_for_edit(self, key: str, target: Path) -> str:
        self._service.download_file(key, target)
        open_file(target)
        return f"已下载到 {target}，修改后用覆盖按钮上传"

    def _edit_target(self, key: str) -> Path:
        safe_name = key.replace("/", "__").replace("\\", "__")
        return Path(tempfile.gettempdir()) / EDIT_DIR_NAME / safe_name

    def _run_task(self, title: str, task, on_success=None, progress_enabled: bool = False) -> None:
        if self._busy:
            self._write_log("已有任务正在执行，请等当前任务完成。")
            return
        self._busy = True
        self._status.setText(f"{title}中...")
        self._last_progress_logged = -10
        self._start_progress(progress_enabled)
        self._write_log(f"开始{title}...")
        thread = QThread()
        worker = TaskWorker(title, task)
        worker.moveToThread(thread)
        self._workers.append(worker)
        worker.progress.connect(self._on_progress)
        worker.succeeded.connect(lambda name, result: self._on_success(name, result, on_success))
        worker.failed.connect(self._on_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(lambda: self._workers.remove(worker))
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._threads.remove(thread))
        thread.finished.connect(self._on_task_finished)
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        thread.started.connect(worker.run)
        thread.start()

    def _start_progress(self, progress_enabled: bool) -> None:
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        if not progress_enabled:
            self._progress.setRange(0, 0)

    def _handle_action(self, action) -> None:
        try:
            action()
        except Exception as exc:
            self._on_error("操作失败", str(exc))

    def _on_task_finished(self) -> None:
        self._busy = False

    def _on_progress(self, consumed, total) -> None:
        total_bytes = int(total or 0)
        consumed_bytes = int(consumed or 0)
        percent = int(consumed_bytes * 100 / total_bytes) if total_bytes else 0
        self._progress.setRange(0, 100)
        self._progress.setValue(percent)
        self._status.setText(f"上传进度 {percent}%")
        self._write_progress_log(percent, consumed_bytes, total_bytes)

    def _write_progress_log(self, percent: int, consumed: int, total: int) -> None:
        if percent < self._last_progress_logged + 10 and percent != 100:
            return
        self._last_progress_logged = percent
        shown = f"{format_size(consumed)}/{format_size(total)}"
        self._write_log(f"上传进度 {percent}% ({shown}, {consumed}/{total} bytes)")


    def _on_success(self, title: str, result, on_success) -> None:
        self._status.setText("完成")
        self._finish_progress(title)
        if on_success:
            on_success(result)
            return
        self._write_log(f"{title}成功: {result}")

    def _finish_progress(self, title: str) -> None:
        self._progress.setRange(0, 100)
        self._progress.setValue(100 if title in UPLOAD_TITLES else 0)

    def _on_error(self, title: str, message: str) -> None:
        self._status.setText("失败")
        self._progress.setRange(0, 100)
        self._write_log(f"{title}失败: {message}")
        QMessageBox.critical(self, title, message)

    def _write_log(self, message: str) -> None:
        self._log.append(message)
        scrollbar = self._log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
