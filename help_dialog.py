from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QWidget

from help_text import HELP_HTML


def show_help_dialog(parent: QWidget) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle("使用帮助 / 作者")
    dialog.resize(680, 520)
    layout = QVBoxLayout(dialog)
    browser = QTextBrowser(dialog)
    browser.setOpenExternalLinks(False)
    browser.setHtml(HELP_HTML)
    browser.anchorClicked.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
    layout.addWidget(browser)
    dialog.exec()
