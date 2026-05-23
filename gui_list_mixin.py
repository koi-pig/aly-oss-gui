from __future__ import annotations

from PySide6.QtCore import Slot


class ListMixin:
    @Slot()
    def refresh(self) -> None:
        prefix = self._prefix.text().strip()
        self._page_markers = [""]
        self._current_prefix = prefix
        self._load_page()

    @Slot()
    def previous_page(self) -> None:
        if len(self._page_markers) <= 1:
            self._write_log("已经是第一页。")
            return
        self._page_markers.pop()
        self._load_page()

    @Slot()
    def next_page(self) -> None:
        if not self._next_marker:
            self._write_log("没有下一页。")
            return
        self._page_markers.append(self._next_marker)
        self._load_page()

    def _load_page(self) -> None:
        prefix = self._current_prefix
        clean = self._service.prefix_from_input(prefix)
        page_no = len(self._page_markers)
        marker = self._page_markers[-1]
        sort_mode = self._sort_mode.currentText()
        self._write_log(f"准备刷新列表，前缀: {clean or '(全部)'}，第 {page_no} 页，排序: {sort_mode}")
        self._run_task("刷新列表", lambda _: self._list_page(prefix, marker), self._show_page)

    def _list_page(self, prefix: str, marker: str):
        if self._sort_mode.currentText() == "最新优先":
            return self._service.list_objects_recent_page(prefix, marker, self._page_size_value())
        return self._service.list_objects_page(prefix, marker, self._page_size_value())
