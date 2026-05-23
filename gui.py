from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from PySide6.QtCore import QThread, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_defs import APP_VERSION, COLUMNS, DEFAULT_EXPIRE_DAYS, LOG_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH, app_base_dir
from config_dialog import ConfigDialog
from gui_data_mixin import DataMixin
from gui_task_mixin import TaskMixin
from help_dialog import show_help_dialog
from oss_config import load_config
from oss_service import BucketOption, OssObject, OssService

class OssMainWindow(DataMixin, TaskMixin, QMainWindow):
    def __init__(self, service: OssService) -> None:
        super().__init__()
        self._service = service
        self._threads: list[QThread] = []
        self._workers: list[object] = []
        self._busy = False
        self._page_markers = [""]
        self._next_marker = ""
        self._current_prefix = ""
        self._last_progress_logged = -10
        self._upload_started_at = 0.0
        self._upload_total_size = 0
        self._last_progress_at, self._last_progress_bytes = 0.0, 0
        self._selected_files: list[Path] = []
        self._selected_file = QLineEdit()
        self._object_key = QLineEdit()
        self._replace_url = QLineEdit()
        self._prefix = QLineEdit()
        self._bucket = QComboBox(); self._bucket.setEditable(True)
        self._link_mode = QComboBox()
        self._expire_days = QLineEdit(str(DEFAULT_EXPIRE_DAYS))
        self._page_size = QLineEdit(str(self._service.page_size))
        self._link_detail = QLineEdit()
        self._last_upload_url = QLineEdit()
        self._page_info = QLabel("总数 0，本页 0")
        self._status = QLabel("就绪")
        self._progress = QProgressBar()
        self._table = QTableWidget(0, len(COLUMNS))
        self._log = QTextEdit()
        self._build()
        self._write_log(f"程序已启动，版本 {APP_VERSION}。当前 Bucket: {self._service.bucket_name}")

    def _build(self) -> None:
        self.setWindowTitle(f"阿里云 OSS 文件管理工具 - by koi-pig - QQ 2557745606 - {APP_VERSION}")
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "assets" / "app.ico")))
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(self._build_upload_layout())
        layout.addLayout(self._build_bucket_layout())
        layout.addLayout(self._build_list_layout())
        layout.addLayout(self._build_action_layout())
        self._log.setReadOnly(True)
        self._log.setFixedHeight(LOG_HEIGHT)
        layout.addWidget(QLabel("操作日志"))
        layout.addWidget(self._log)
        self.setCentralWidget(root)

    def _build_upload_layout(self) -> QGridLayout:
        layout = QGridLayout()
        layout.addWidget(self._button("选择文件", self.choose_file), 0, 0)
        layout.addWidget(self._selected_file, 0, 1)
        layout.addWidget(QLabel("OSS 路径"), 0, 2)
        layout.addWidget(self._object_key, 0, 3)
        layout.addWidget(self._button("上传", self.upload), 0, 4)
        layout.addWidget(self._button("使用帮助 / 作者", self.show_help), 0, 5)
        layout.addWidget(QLabel("原链接"), 1, 0)
        layout.addWidget(self._replace_url, 1, 1, 1, 3)
        layout.addWidget(self._button("按原链接替换", self.replace_by_url), 1, 4, 1, 2)
        self._link_mode.addItems(("永不过期公开链接", "签名链接"))
        layout.addWidget(QLabel("上传链接"), 2, 0)
        layout.addWidget(self._link_mode, 2, 1)
        layout.addWidget(QLabel("过期天数"), 2, 2)
        layout.addWidget(self._expire_days, 2, 3)
        self._last_upload_url.setReadOnly(True)
        layout.addWidget(QLabel("最后上传链接"), 3, 0)
        layout.addWidget(self._last_upload_url, 3, 1, 1, 3)
        layout.addWidget(self._button("复制上传链接", self.copy_last_upload_url), 3, 4, 1, 2)
        return layout

    def _build_bucket_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self._bucket.addItem(self._service.bucket_name)
        self._bucket.currentTextChanged.connect(self.change_bucket)
        layout.addWidget(QLabel("Bucket"))
        layout.addWidget(self._bucket)
        layout.addWidget(self._button("刷新 Bucket", self.refresh_buckets))
        layout.addWidget(self._button("测试连接", self.test_connection))
        layout.addWidget(self._button("OSS 配置", self.edit_oss_config))
        layout.addWidget(self._button("打开配置文件", self.open_config))
        return layout

    def _build_list_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        search = QHBoxLayout()
        self._prefix.setPlaceholderText("例如 apps/，也可以粘贴完整 OSS 链接")
        search.addWidget(QLabel("前缀"))
        search.addWidget(self._prefix)
        search.addWidget(QLabel("每页"))
        search.addWidget(self._page_size)
        search.addWidget(self._button("刷新列表", self.refresh))
        layout.addLayout(search)
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._show_selected_link)
        layout.addWidget(self._table)
        self._link_detail.setReadOnly(True)
        layout.addWidget(QLabel("选中文件完整链接"))
        layout.addWidget(self._link_detail)
        return layout

    def _build_action_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        for text, command in self._actions():
            layout.addWidget(self._button(text, command))
        layout.addWidget(self._button("上一页", self.previous_page))
        layout.addWidget(self._button("下一页", self.next_page))
        layout.addWidget(self._button("统计总数", self.count_total))
        layout.addWidget(self._page_info)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        layout.addWidget(self._status)
        return layout

    def _actions(self) -> tuple[tuple[str, object], ...]:
        return (
            ("复制公开链接", self.copy_public_url),
            ("复制签名链接", self.copy_signed_url),
            ("下载并打开修改", self.download_and_open),
            ("用本地文件覆盖选中项", self.overwrite_selected),
            ("删除选中文件", self.delete_selected),
        )

    def _button(self, text: str, command) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda checked=False: self._handle_action(command))
        return button

    @Slot()
    def choose_file(self) -> None:
        filenames, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        if not filenames:
            return
        self._selected_files = [Path(name) for name in filenames]
        text = "; ".join(str(path) for path in self._selected_files)
        self._selected_file.setText(text)
        self._object_key.setText(self._object_key_for_file(self._selected_files[0]))

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
        self._write_log(f"准备刷新列表，前缀: {clean or '(全部)'}，第 {page_no} 页")
        self._run_task("刷新列表", lambda _: self._service.list_objects_page(prefix, marker, self._page_size_value()), self._show_page)

    @Slot()
    def refresh_buckets(self) -> None:
        self._run_task("刷新 Bucket", lambda _: self._service.list_buckets(), self._show_buckets)

    @Slot()
    def test_connection(self) -> None:
        self._run_task("测试连接", lambda _: self._service.list_objects("apps/"), self._show_test_result)

    @Slot()
    def change_bucket(self, bucket_name: str) -> None:
        try:
            name = self._selected_bucket_name(bucket_name)
            self._service.use_bucket(name)
            self._write_log(f"当前 Bucket: {self._service.bucket_name}")
        except Exception as exc:
            self._write_log(f"切换 Bucket 失败: {exc}")

    def _selected_bucket_name(self, text: str) -> str:
        data = self._bucket.currentData()
        if data:
            return str(data)
        return text.split(" -> ", 1)[0].strip()

    def _show_buckets(self, options: list[BucketOption]) -> None:
        current = self._service.bucket_name
        self._bucket.blockSignals(True)
        self._bucket.clear()
        for option in options:
            self._bucket.addItem(option.label, option.name)
        self._bucket.setCurrentText(self._bucket_label(options, current))
        self._bucket.blockSignals(False)
        self._write_log(f"Bucket 已刷新，共 {len(options)} 个")

    def _bucket_label(self, options: list[BucketOption], current: str) -> str:
        for option in options:
            if option.name == current:
                return option.label
        return current

    def _show_test_result(self, objects: list[OssObject]) -> None:
        names = ", ".join(item.key for item in objects[:5]) or "无文件"
        self._write_log(f"连接正常。apps/ 返回 {len(objects)} 个文件：{names}")

    @Slot()
    def show_help(self) -> None:
        show_help_dialog(self)

    @Slot()
    def copy_public_url(self) -> None:
        self._copy_text(self._service.public_url(self._selected_key()))

    @Slot()
    def copy_signed_url(self) -> None:
        seconds = self._expire_days_value() * 24 * 60 * 60
        self._copy_text(self._service.signed_url(self._selected_key(), seconds))

    @Slot()
    def download_and_open(self) -> None:
        key = self._selected_key()
        self._run_task("下载文件", lambda _: self._download_for_edit(key, self._edit_target(key)))

    @Slot()
    def delete_selected(self) -> None:
        key = self._selected_key()
        message = "确定删除这个文件吗？\n" + key
        reply = QMessageBox.question(self, "确认删除", message)
        if reply == QMessageBox.Yes:
            task = lambda _: self._service.delete_file(key)
            self._run_task("删除文件", task, lambda _: self.refresh())


def main() -> None:
    app = QApplication(sys.argv)
    base_dir = app_base_dir()
    if not (base_dir / "config.local.json").exists():
        if ConfigDialog(base_dir).exec() != QDialog.Accepted:
            return
    config = load_config(base_dir)
    window = OssMainWindow(OssService(config))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
