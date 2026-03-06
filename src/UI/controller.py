"""controller.py
-UI的控制逻辑层
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid

from PySide6.QtCore import QObject, QRect, Signal, Slot, QThread
from PySide6.QtGui import QGuiApplication

from src.OCRAgent.openai_ocr import ocr as openai_ocr
from src.TranslateAgent.openai_translate import translate as openai_translate
from src.UI.overlay import RegionOverlay
from src.UI.popup import TranslationPopup


class OCRTranslateWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, image_path: str) -> None:
        super().__init__()
        self._image_path = image_path

    @Slot()
    def run(self) -> None:
        try:
            source_text = openai_ocr(self._image_path)
            if not source_text.strip():
                raise ValueError("OCR returned empty text")
            translated = openai_translate(source_text)
            self.finished.emit(translated)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            if os.path.exists(self._image_path):
                os.remove(self._image_path)


class UIController(QObject):
    status_changed = Signal(str)

    def __init__(self, popup: TranslationPopup) -> None:
        super().__init__()
        self._popup = popup
        self._selected_region: QRect | None = None
        self._overlay: RegionOverlay | None = None
        self._worker_thread: QThread | None = None
        self._worker: OCRTranslateWorker | None = None
        self._is_busy = False

    @property
    def selected_region(self) -> QRect | None:
        return self._selected_region

    def start_region_selection(self) -> None:
        self._overlay = RegionOverlay()
        self._overlay.region_selected.connect(self._on_region_selected)
        self._overlay.selection_cancelled.connect(self._on_selection_cancelled)

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.status_changed.emit("No available screen for selection")
            return

        self.status_changed.emit("Select translation area by dragging mouse")
        self._overlay.start(screen.virtualGeometry())

    @Slot()
    def trigger_capture_and_translate(self) -> None:
        if self._is_busy:
            self.status_changed.emit("Translation is already running")
            return

        if self._selected_region is None:
            self.status_changed.emit("Please select region first")
            return

        try:
            image_path = self._capture_selected_region(self._selected_region)
        except Exception as error:
            self.status_changed.emit(f"Capture failed: {error}")
            return

        self._worker_thread = QThread(self)
        self._worker = OCRTranslateWorker(image_path)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._on_translation_finished)
        self._worker.failed.connect(self._on_translation_failed)
        self._worker_thread.finished.connect(self._cleanup_worker)

        self._is_busy = True
        self._worker_thread.start()

        self.status_changed.emit("Captured image, OCR + translation running")

    @Slot(QRect)
    def _on_region_selected(self, rect: QRect) -> None:
        self._selected_region = rect
        self.status_changed.emit(
            f"Region selected: {rect.width()}x{rect.height()} at ({rect.x()}, {rect.y()})"
        )

    @Slot()
    def _on_selection_cancelled(self) -> None:
        self.status_changed.emit("Region selection cancelled")

    @Slot(str)
    def _on_translation_finished(self, translated_text: str) -> None:
        self._popup.set_text(translated_text)
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()
        self._is_busy = False
        self.status_changed.emit("Translation complete")

    @Slot(str)
    def _on_translation_failed(self, message: str) -> None:
        self._popup.set_text(f"Error: {message}")
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()
        self._is_busy = False
        self.status_changed.emit("Translation failed")

    def _capture_selected_region(self, rect: QRect) -> str:
        image_path = os.path.join(
            tempfile.gettempdir(),
            f"rainyocr_capture_{uuid.uuid4().hex}.png",
        )

        if self._is_wayland_session():
            if self._capture_with_grim(rect, image_path):
                return image_path
            raise RuntimeError(
                "Wayland session detected and grim capture unavailable. "
                "Please install/configure grim."
            )

        screen = QGuiApplication.screenAt(rect.center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("No screen available")

        dpr = screen.devicePixelRatio()
        geometry = screen.geometry()
        x = int((rect.x() - geometry.x()) * dpr)
        y = int((rect.y() - geometry.y()) * dpr)
        width = int(rect.width() * dpr)
        height = int(rect.height() * dpr)

        pixmap = screen.grabWindow(
            0,
            x,
            y,
            width,
            height,
        )

        if pixmap.isNull():
            raise RuntimeError("Captured image is empty")

        saved = pixmap.save(image_path, "PNG")
        if not saved:
            raise RuntimeError("Failed to save captured image")

        return image_path

    def _is_wayland_session(self) -> bool:
        return bool(os.getenv("WAYLAND_DISPLAY"))

    def _capture_with_grim(self, rect: QRect, image_path: str) -> bool:
        grim_path = shutil.which("grim")
        if grim_path is None:
            if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
                raise RuntimeError(
                    "Hyprland detected but 'grim' is not installed. "
                    "Please install grim and retry."
                )
            return False

        geometry = f"{rect.x()},{rect.y()} {rect.width()}x{rect.height()}"
        result = subprocess.run(
            [grim_path, "-g", geometry, image_path],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
                stderr = result.stderr.strip() or "unknown grim error"
                raise RuntimeError(f"grim capture failed: {stderr}")
            return False

        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
                raise RuntimeError("grim capture produced empty image")
            return False

        return True

    @Slot()
    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()

        if self._worker_thread is not None:
            self._worker_thread.deleteLater()

        self._worker_thread = None
        self._worker = None

    def shutdown(self) -> None:
        if self._worker_thread is not None and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(1500)
