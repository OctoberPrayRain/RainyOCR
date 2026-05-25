"""overlay.py
-遮罩框选区域
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RegionOverlay(QWidget):
    region_selected = Signal(QRect)
    selection_cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._drag_start = QPoint()
        self._drag_end = QPoint()
        self._is_dragging = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def start(self, geometry: QRect) -> None:
        self.setGeometry(geometry)
        self.show()
        self.raise_()
        self.activateWindow()

    def current_global_rect(self) -> QRect:
        return QRect(self._drag_start, self._drag_end).normalized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start = event.globalPosition().toPoint()
            self._drag_end = self._drag_start
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.selection_cancelled.emit()
            self.close()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging:
            self._drag_end = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self._is_dragging = False
        self._drag_end = event.globalPosition().toPoint()
        rect = self.current_global_rect()

        if rect.width() >= 10 and rect.height() >= 10:
            self.region_selected.emit(rect)
        else:
            self.selection_cancelled.emit()

        self.close()

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(5, 12, 20, 132))

        if self._is_dragging or not self.current_global_rect().isNull():
            selection = self.current_global_rect()
            local_selection = QRect(
                self.mapFromGlobal(selection.topLeft()),
                self.mapFromGlobal(selection.bottomRight()),
            ).normalized()
            painter.fillRect(local_selection, QColor(53, 210, 255, 34))
            pen = QPen(QColor(53, 210, 255), 3)
            painter.setPen(pen)
            painter.drawRect(local_selection)
