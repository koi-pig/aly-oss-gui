from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class TaskWorker(QObject):
    succeeded = Signal(str, object)
    failed = Signal(str, str)
    progress = Signal(object, object)
    finished = Signal()

    def __init__(self, title: str, task) -> None:
        super().__init__()
        self._title = title
        self._task = task

    @Slot()
    def run(self) -> None:
        try:
            result = self._task(self.progress.emit)
            self.succeeded.emit(self._title, result)
        except Exception as exc:
            self.failed.emit(self._title, str(exc))
        finally:
            self.finished.emit()
