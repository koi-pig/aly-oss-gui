from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from oss_config import read_config_data, save_config_data


FIELD_LABELS = (
    ("access_key_id", "AccessKey ID"),
    ("access_key_secret", "AccessKey Secret"),
    ("bucket", "默认 Bucket"),
    ("endpoint", "Endpoint"),
    ("view_endpoint", "链接模板"),
    ("signed_url_expire_seconds", "签名默认秒数"),
    ("page_size", "默认每页数量"),
    ("multipart_threshold_mb", "分片阈值 MB"),
    ("multipart_part_size_mb", "每片大小 MB"),
    ("multipart_threads", "上传线程数"),
)
REQUIRED_KEYS = ("access_key_id", "access_key_secret", "bucket", "endpoint")
INT_KEYS = (
    "signed_url_expire_seconds",
    "page_size",
    "multipart_threshold_mb",
    "multipart_part_size_mb",
    "multipart_threads",
)


class ConfigDialog(QDialog):
    def __init__(self, base_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._base_dir = base_dir
        self._fields = {key: QLineEdit() for key, _ in FIELD_LABELS}
        self._build()
        self._load()

    def _build(self) -> None:
        self.setWindowTitle("阿里云 OSS 配置")
        self.resize(680, 380)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for key, label in FIELD_LABELS:
            form.addRow(label, self._fields[key])
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        data = read_config_data(self._base_dir)
        for key, field in self._fields.items():
            field.setText(str(data.get(key, "")))

    def _save(self) -> None:
        try:
            save_config_data(self._base_dir, self._validated_data())
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "配置保存失败", str(exc))

    def _validated_data(self) -> dict[str, object]:
        data = {key: field.text().strip() for key, field in self._fields.items()}
        missing = [key for key in REQUIRED_KEYS if not data[key]]
        if missing:
            raise ValueError(f"请填写必填配置: {', '.join(missing)}")
        for key in INT_KEYS:
            data[key] = self._positive_int(key)
        return data

    def _positive_int(self, key: str) -> int:
        value = int(self._fields[key].text().strip())
        if value <= 0:
            raise ValueError(f"{key} 必须大于 0")
        return value
