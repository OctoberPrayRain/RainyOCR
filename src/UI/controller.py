"""controller.py
-UI的控制逻辑层
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

from PIL import Image
from PySide6.QtCore import QObject, QRect, Signal, Slot, QThread
from PySide6.QtGui import QGuiApplication, QImage, QPixmap, QScreen

from src.OCRAgent.openai_ocr import ocr as openai_ocr
from src.TranslateAgent.openai_translate import translate as openai_translate
from src.UI.overlay import RegionOverlay
from src.UI.popup import TranslationPopup


logger = logging.getLogger("rainyocr.ui.controller")


class OCRTranslateWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, image_path: str) -> None:
        super().__init__()
        self._image_path = image_path

    @Slot()
    def run(self) -> None:
        try:
            logger.info("OCR worker started; image_path=%s", self._image_path)
            source_text = openai_ocr(self._image_path)
            logger.info("OCR completed; text_length=%s", len(source_text))
            if not source_text.strip():
                raise ValueError("OCR returned empty text")
            translated = openai_translate(source_text)
            logger.info("Translation completed; text_length=%s", len(translated))
            self.finished.emit(translated)
        except Exception as error:
            logger.exception("OCR/translation worker failed")
            self.failed.emit(str(error))
        finally:
            if os.path.exists(self._image_path):
                os.remove(self._image_path)
                logger.info("Temporary capture removed: %s", self._image_path)


class UIController(QObject):
    status_changed = Signal(str)
    translation_displayed = Signal()

    def __init__(self, popup: TranslationPopup) -> None:
        super().__init__()
        self._popup = popup
        self._selected_region: QRect | None = None
        self._overlay: RegionOverlay | None = None
        self._worker_thread: QThread | None = None
        self._worker: OCRTranslateWorker | None = None
        self._is_busy = False
        self._active_capture_hash: str | None = None
        self._last_capture_hash: str | None = None
        self._last_translation: str | None = None

    @property
    def selected_region(self) -> QRect | None:
        return self._selected_region

    def start_region_selection(self) -> None:
        logger.info("Starting region selection")
        self._overlay = RegionOverlay()
        self._overlay.region_selected.connect(self._on_region_selected)
        self._overlay.selection_cancelled.connect(self._on_selection_cancelled)

        selection_geometry = self._virtual_screen_geometry()
        if selection_geometry.isEmpty():
            logger.warning("No available screen geometry for region selection")
            self.status_changed.emit("No available screen for selection")
            return

        logger.info(
            "Region selection geometry: x=%s y=%s w=%s h=%s",
            selection_geometry.x(),
            selection_geometry.y(),
            selection_geometry.width(),
            selection_geometry.height(),
        )
        self.status_changed.emit("Select translation area by dragging mouse")
        self._overlay.start(selection_geometry)

    @Slot()
    def trigger_capture_and_translate(self) -> None:
        logger.info("Capture/translate requested")
        if self._is_busy:
            logger.info("Capture ignored because worker is already busy")
            self.status_changed.emit("Translation is already running")
            return

        if self._selected_region is None:
            logger.info("Capture ignored because no region is selected")
            self.status_changed.emit("Please select region first")
            return

        try:
            image_path = self._capture_selected_region(self._selected_region)
            capture_hash = self._file_sha256(image_path)
        except Exception as error:
            logger.exception("Capture failed")
            self.status_changed.emit(f"Capture failed: {error}")
            return

        if (
            capture_hash == self._last_capture_hash
            and self._last_translation is not None
        ):
            os.remove(image_path)
            logger.info("Reusing cached translation for identical capture")
            self._show_translation(self._last_translation)
            self.status_changed.emit("Translation reused from identical capture")
            return

        self._active_capture_hash = capture_hash

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
        self._popup.set_title("Translating...")
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()
        self.translation_displayed.emit()
        self._worker_thread.start()
        logger.info("OCR worker thread started")

        self.status_changed.emit("Captured image, OCR + translation running")

    @Slot(QRect)
    def _on_region_selected(self, rect: QRect) -> None:
        self._selected_region = rect
        logger.info(
            "Region selected: x=%s y=%s w=%s h=%s",
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height(),
        )
        self.status_changed.emit(
            f"Region selected: {rect.width()}x{rect.height()} at ({rect.x()}, {rect.y()})"
        )

    @Slot()
    def _on_selection_cancelled(self) -> None:
        logger.info("Region selection cancelled")
        self.status_changed.emit("Region selection cancelled")

    @Slot(str)
    def _on_translation_finished(self, translated_text: str) -> None:
        logger.info("Translation finished; translated_text_length=%s", len(translated_text))
        self._last_capture_hash = self._active_capture_hash
        self._last_translation = translated_text
        self._active_capture_hash = None
        self._show_translation(translated_text)
        self._is_busy = False
        self.status_changed.emit("Translation complete")

    def _show_translation(self, translated_text: str) -> None:
        logger.info("Showing translation popup; text_length=%s", len(translated_text))
        self._popup.set_title("Translation")
        self._popup.set_text(translated_text)
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()
        self.translation_displayed.emit()

    @Slot(str)
    def _on_translation_failed(self, message: str) -> None:
        logger.error("Translation failed: %s", message)
        self._active_capture_hash = None
        self._popup.set_title("Translation Failed")
        self._popup.set_text(f"Error: {message}")
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()
        self.translation_displayed.emit()
        self._is_busy = False
        self.status_changed.emit("Translation failed")

    def _capture_selected_region(self, rect: QRect) -> str:
        logger.info(
            "Capturing selected region: x=%s y=%s w=%s h=%s wayland=%s",
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height(),
            self._is_wayland_session(),
        )
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

        screen, capture_rect = self._capture_target(rect)
        logger.info(
            "Capture target: screen=%s dpr=%s screen_geometry=(%s,%s %sx%s) rect=(%s,%s %sx%s)",
            screen.name(),
            screen.devicePixelRatio(),
            screen.geometry().x(),
            screen.geometry().y(),
            screen.geometry().width(),
            screen.geometry().height(),
            capture_rect.x(),
            capture_rect.y(),
            capture_rect.width(),
            capture_rect.height(),
        )

        x, y, width, height = self._grab_window_coordinates(screen, capture_rect)
        logger.info(
            "grabWindow coordinates: strategy=%s x=%s y=%s w=%s h=%s",
            self._grab_window_coordinate_strategy(),
            x,
            y,
            width,
            height,
        )

        pixmap = screen.grabWindow(
            0,
            x,
            y,
            width,
            height,
        )
        logger.info(
            "Screen grab completed; pixmap_is_null=%s pixmap_size=%sx%s pixmap_dpr=%s",
            pixmap.isNull(),
            pixmap.width(),
            pixmap.height(),
            pixmap.devicePixelRatio(),
        )

        if pixmap.isNull():
            raise RuntimeError("Captured image is empty")

        self._save_captured_pixmap(pixmap, image_path)

        logger.info("Capture saved: %s size=%s", image_path, os.path.getsize(image_path))
        return image_path

    def _grab_window_coordinates(
        self,
        screen: QScreen,
        capture_rect: QRect,
    ) -> tuple[int, int, int, int]:
        x = capture_rect.x()
        y = capture_rect.y()
        width = capture_rect.width()
        height = capture_rect.height()

        if self._grab_window_coordinate_strategy() == "device-pixel":
            geometry = screen.geometry()
            x -= geometry.x()
            y -= geometry.y()
            dpr = screen.devicePixelRatio()
            return (
                round(x * dpr),
                round(y * dpr),
                round(width * dpr),
                round(height * dpr),
            )

        return x, y, width, height

    def _grab_window_coordinate_strategy(self) -> str:
        if sys.platform in {"win32", "darwin"}:
            return "logical"

        return "device-pixel"

    def _save_captured_pixmap(self, pixmap: QPixmap, image_path: str) -> None:
        if sys.platform == "darwin":
            self._save_captured_pixmap_with_pillow(pixmap, image_path)
            return

        saved = pixmap.save(image_path, "PNG")
        if not saved:
            raise RuntimeError("Failed to save captured image")

    def _save_captured_pixmap_with_pillow(
        self,
        pixmap: QPixmap,
        image_path: str,
    ) -> None:
        logger.info("Saving macOS capture through QImage/Pillow path")
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width = image.width()
        height = image.height()
        byte_count = image.sizeInBytes()
        bytes_per_line = image.bytesPerLine()
        if width <= 0 or height <= 0 or byte_count <= 0:
            raise RuntimeError("Captured image has invalid dimensions")

        buffer = image.constBits()
        image_bytes = bytes(buffer[:byte_count])
        pil_image = Image.frombytes(
            "RGBA",
            (width, height),
            image_bytes,
            "raw",
            "RGBA",
            bytes_per_line,
            1,
        )
        pil_image.save(image_path, "PNG")

    def _file_sha256(self, path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    def _capture_target(self, rect: QRect) -> tuple[QScreen, QRect]:
        normalized_rect = rect.normalized()
        screen = self._screen_for_rect(normalized_rect)
        if screen is None:
            raise RuntimeError("No screen available")

        capture_rect = self._clamp_rect_to_screen(normalized_rect, screen)
        if capture_rect.isEmpty():
            raise RuntimeError("Selected region is outside the active screen")

        return screen, capture_rect

    def _capture_virtual_target(self, rect: QRect) -> QRect:
        capture_rect = self._clamp_rect_to_geometry(
            rect.normalized(),
            self._virtual_screen_geometry(),
        )
        if capture_rect.isEmpty():
            raise RuntimeError("Selected region is outside the active screen")

        return capture_rect

    def _virtual_screen_geometry(self) -> QRect:
        screens = QGuiApplication.screens()
        if not screens:
            logger.warning("QGuiApplication.screens() returned no screens")
            return QRect()

        geometry = QRect(screens[0].geometry())
        for screen in screens[1:]:
            geometry = geometry.united(screen.geometry())

        return geometry

    def _clamp_rect_to_screen(self, rect: QRect, screen: QScreen) -> QRect:
        return self._clamp_rect_to_geometry(rect, screen.geometry())

    def _clamp_rect_to_geometry(self, rect: QRect, geometry: QRect) -> QRect:
        geometry_left = geometry.x()
        geometry_top = geometry.y()
        geometry_right = geometry_left + geometry.width()
        geometry_bottom = geometry_top + geometry.height()

        rect_left = rect.x()
        rect_top = rect.y()
        rect_right = rect.x() + rect.width()
        rect_bottom = rect.y() + rect.height()

        left = min(max(rect_left, geometry_left), geometry_right)
        top = min(max(rect_top, geometry_top), geometry_bottom)
        right = max(min(rect_right, geometry_right), left)
        bottom = max(min(rect_bottom, geometry_bottom), top)

        return QRect(left, top, right - left, bottom - top)

    def _screen_for_rect(self, rect: QRect) -> QScreen | None:
        screen = QGuiApplication.screenAt(rect.center())
        if screen is not None:
            return screen

        best_screen: QScreen | None = None
        best_area = 0
        for candidate in QGuiApplication.screens():
            intersection = self._clamp_rect_to_screen(rect, candidate)
            area = intersection.width() * intersection.height()
            if area > best_area:
                best_screen = candidate
                best_area = area

        if best_screen is not None:
            return best_screen

        return QGuiApplication.primaryScreen()

    def _is_wayland_session(self) -> bool:
        return bool(os.getenv("WAYLAND_DISPLAY"))

    def _capture_with_grim(self, rect: QRect, image_path: str) -> bool:
        grim_path = shutil.which("grim")
        if grim_path is None:
            logger.info("grim not found for Wayland capture")
            if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
                raise RuntimeError(
                    "Hyprland detected but 'grim' is not installed. "
                    "Please install grim and retry."
                )
            return False

        capture_rect = self._capture_virtual_target(rect)
        screens = self._screens_for_rect(capture_rect)
        if len(screens) == 1:
            screen = screens[0]
            screen_rect = self._clamp_rect_to_screen(capture_rect, screen)
            result = self._run_grim_screen_capture(
                grim_path,
                image_path,
                screen_rect,
                screen,
            )
        else:
            result = self._run_grim_capture(grim_path, image_path, capture_rect)

        if result.returncode != 0:
            logger.warning(
                "grim capture failed; returncode=%s stderr=%s",
                result.returncode,
                result.stderr.strip(),
            )
            screen, fallback_rect = self._capture_target(capture_rect)
            result = self._run_grim_screen_capture(
                grim_path,
                image_path,
                fallback_rect,
                screen,
                result,
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

    def _screens_for_rect(self, rect: QRect) -> list[QScreen]:
        screens: list[QScreen] = []
        for screen in QGuiApplication.screens():
            if not self._clamp_rect_to_screen(rect, screen).isEmpty():
                screens.append(screen)

        return screens

    def _run_grim_capture(
        self,
        grim_path: str,
        image_path: str,
        rect: QRect,
    ) -> subprocess.CompletedProcess[str]:
        geometry = f"{rect.x()},{rect.y()} {rect.width()}x{rect.height()}"
        logger.info("Running grim capture: geometry=%s", geometry)
        return subprocess.run(
            [grim_path, "-g", geometry, image_path],
            check=False,
            capture_output=True,
            text=True,
        )

    def _run_grim_screen_capture(
        self,
        grim_path: str,
        image_path: str,
        rect: QRect,
        screen: QScreen,
        original_result: subprocess.CompletedProcess[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if original_result is None:
            original_result = subprocess.CompletedProcess([grim_path], 1, "", "")

        if not screen.name():
            logger.warning("Cannot run grim output capture because screen has no name")
            return original_result

        full_output_path = os.path.join(
            tempfile.gettempdir(),
            f"rainyocr_full_output_{uuid.uuid4().hex}.png",
        )
        output_result = subprocess.run(
            [grim_path, "-o", screen.name(), full_output_path],
            check=False,
            capture_output=True,
            text=True,
        )
        if output_result.returncode != 0:
            logger.warning(
                "grim output capture failed; returncode=%s stderr=%s",
                output_result.returncode,
                output_result.stderr.strip(),
            )
            return original_result

        try:
            self._crop_grim_output(full_output_path, image_path, rect, screen)
        except OSError:
            return original_result
        finally:
            if os.path.exists(full_output_path):
                os.remove(full_output_path)

        return subprocess.CompletedProcess(
            original_result.args,
            0,
            original_result.stdout,
            original_result.stderr,
        )

    def _crop_grim_output(
        self,
        source_path: str,
        target_path: str,
        rect: QRect,
        screen: QScreen,
    ) -> None:
        screen_geometry = screen.geometry()
        with Image.open(source_path) as image:
            scale_x = image.width / screen_geometry.width()
            scale_y = image.height / screen_geometry.height()
            left = self._clamp_pixel(
                round((rect.x() - screen_geometry.x()) * scale_x),
                image.width,
            )
            top = self._clamp_pixel(
                round((rect.y() - screen_geometry.y()) * scale_y),
                image.height,
            )
            right = self._clamp_pixel(
                round((rect.x() + rect.width() - screen_geometry.x()) * scale_x),
                image.width,
            )
            bottom = self._clamp_pixel(
                round((rect.y() + rect.height() - screen_geometry.y()) * scale_y),
                image.height,
            )
            if right <= left or bottom <= top:
                raise OSError("Cropped grim image is empty")

            cropped = image.crop((left, top, right, bottom))
            cropped.save(target_path, "PNG")

    def _clamp_pixel(self, value: int, limit: int) -> int:
        return min(max(value, 0), limit)

    @Slot()
    def _cleanup_worker(self) -> None:
        logger.info("Cleaning up OCR worker")
        if self._worker is not None:
            self._worker.deleteLater()

        if self._worker_thread is not None:
            self._worker_thread.deleteLater()

        self._worker_thread = None
        self._worker = None

    def shutdown(self) -> None:
        logger.info("Controller shutdown requested")
        if self._worker_thread is not None and self._worker_thread.isRunning():
            self._worker_thread.quit()
            stopped = self._worker_thread.wait(1500)
            if stopped:
                logger.info("Worker thread stopped during shutdown")
            else:
                logger.warning("Worker thread did not stop within shutdown timeout")
