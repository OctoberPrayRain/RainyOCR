"""app.py
-前端UI的主程序接口
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.UI.controller import UIController
from src.UI.popup import TranslationPopup
from src.UI.settings import (
    DEFAULT_CAPTURE_SHORTCUT,
    AppSettings,
    SettingsDialog,
    load_settings,
)
from src.UI.style import APP_STYLESHEET, add_soft_shadow, stylesheet_for_theme
from src.UI.tray import RainyTray
from src.UI.window_chrome import (
    WindowDragController,
    enable_translucent_frameless_window,
    is_macos,
)

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class GlobalHotkeyListener(QObject):
    triggered = Signal()
    status_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._listener = None

    def start(self, shortcut: str) -> None:
        self.stop()
        if keyboard is None:
            self.status_changed.emit(
                "Global hotkey unavailable, using app shortcut only"
            )
            return

        hotkey = self._pynput_hotkey(shortcut)
        if not hotkey:
            self.status_changed.emit(
                f"Global hotkey unavailable for shortcut: {shortcut}"
            )
            return

        try:
            self._listener = keyboard.GlobalHotKeys(
                {
                    hotkey: self.triggered.emit,
                }
            )
            self._listener.start()
        except Exception as error:
            self._listener = None
            self.status_changed.emit(
                f"Global hotkey unavailable for {shortcut}: {error}"
            )
            return

        self.status_changed.emit(f"Global hotkey active: {shortcut}")

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _pynput_hotkey(self, shortcut: str) -> str:
        parts = [part.strip() for part in shortcut.split("+") if part.strip()]
        if not parts:
            return ""

        converted: list[str] = []
        key_map = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "meta": "<cmd>",
            "super": "<cmd>",
            "win": "<cmd>",
            "cmd": "<cmd>",
            "return": "<enter>",
            "enter": "<enter>",
            "esc": "<esc>",
            "escape": "<esc>",
            "space": "<space>",
            "tab": "<tab>",
            "backspace": "<backspace>",
            "del": "<delete>",
            "delete": "<delete>",
            "ins": "<insert>",
            "insert": "<insert>",
            "home": "<home>",
            "end": "<end>",
            "pgup": "<page_up>",
            "pageup": "<page_up>",
            "pgdown": "<page_down>",
            "pagedown": "<page_down>",
            "left": "<left>",
            "right": "<right>",
            "up": "<up>",
            "down": "<down>",
        }
        for part in parts:
            lower_part = part.lower()
            if lower_part.startswith("f") and lower_part[1:].isdigit():
                converted.append(f"<{lower_part}>")
                continue

            converted.append(key_map.get(lower_part, lower_part))

        return "+".join(converted)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RainyOCR")
        enable_translucent_frameless_window(self)
        self.resize(520, 360)

        self._settings = load_settings()
        self._popup = TranslationPopup()
        self._controller = UIController(self._popup)
        self._global_hotkey = GlobalHotkeyListener()
        self._allow_close = False
        self._is_dark_theme = False
        self._drag_controller = WindowDragController(self)

        central = QWidget(self)
        central.setObjectName("mainCentral")
        if not is_macos():
            central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        card = QFrame(central)
        card.setObjectName("heroCard")
        add_soft_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 24)
        card_layout.setSpacing(18)

        title = QLabel("RainyOCR")
        title.setObjectName("appTitle")
        self._settings_button = QPushButton("⚙")
        self._settings_button.setObjectName("settingsGearButton")
        self._settings_button.setToolTip("Settings")
        self._settings_button.setFixedSize(42, 42)
        self._theme_button = QPushButton("☾")
        self._theme_button.setObjectName("themeToggleButton")
        self._theme_button.setToolTip("Switch to dark mode")
        self._theme_button.setFixedSize(42, 42)
        self._close_button = QPushButton("×")
        self._close_button.setObjectName("windowCloseButton")
        self._close_button.setToolTip("Close")
        self._close_button.setFixedSize(42, 42)

        subtitle = QLabel(
            "Capture game text, OCR it, and translate without leaving your screen."
        )
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)

        self._status_label = QLabel("Ready. Step 1: Select Region")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setWordWrap(True)

        self._select_button = QPushButton("Select Region")
        self._select_button.setObjectName("secondaryButton")
        self._trigger_button = QPushButton("Capture + Translate")
        self._trigger_button.setObjectName("primaryButton")
        self._shortcut_hint = QLabel()
        self._shortcut_hint.setObjectName("shortcutHint")
        self._shortcut_hint.setAlignment(Qt.AlignmentFlag.AlignRight)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addWidget(self._select_button)
        button_row.addWidget(self._trigger_button)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self._theme_button)
        title_row.addWidget(self._settings_button)
        title_row.addWidget(self._close_button)

        card_layout.addLayout(title_row)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self._status_label)
        card_layout.addLayout(button_row)
        card_layout.addWidget(self._shortcut_hint)

        layout.addWidget(card)

        self.setCentralWidget(central)

        self._select_button.clicked.connect(self._controller.start_region_selection)
        self._trigger_button.clicked.connect(
            self._controller.trigger_capture_and_translate
        )
        self._settings_button.clicked.connect(self._open_settings)
        self._theme_button.clicked.connect(self._toggle_theme)
        self._close_button.clicked.connect(self.close)
        self._controller.status_changed.connect(self._set_status)
        self._controller.translation_displayed.connect(self._hide_to_tray)

        self._tray = RainyTray(
            self,
            self._restore_from_tray,
            self._show_translation_popup,
            self._open_settings,
            self._controller.trigger_capture_and_translate,
            self._quit_application,
        )
        self._tray.show()

        self._shortcut = QShortcut(QKeySequence(), self)
        self._shortcut.activated.connect(self._controller.trigger_capture_and_translate)

        self._global_hotkey.triggered.connect(
            self._controller.trigger_capture_and_translate,
        )
        self._global_hotkey.status_changed.connect(self._set_status)
        self._apply_settings(self._settings)

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)

    @Slot()
    def _toggle_theme(self) -> None:
        self._is_dark_theme = not self._is_dark_theme
        application = QApplication.instance()
        if isinstance(application, QApplication):
            application.setStyleSheet(stylesheet_for_theme(self._is_dark_theme))

        self._sync_theme_button()

    def _sync_theme_button(self) -> None:
        if self._is_dark_theme:
            self._theme_button.setText("☀")
            self._theme_button.setToolTip("Switch to light mode")
            return

        self._theme_button.setText("☾")
        self._theme_button.setToolTip("Switch to dark mode")

    @Slot()
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    @Slot(AppSettings)
    def _on_settings_saved(self, settings: AppSettings) -> None:
        self._apply_settings(settings)
        self._set_status("Settings saved. Shortcut and model config are active.")

    def _apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        self._popup.set_translation_font_size(settings.translation_font_size)
        self._apply_shortcut(settings.capture_shortcut)

    def _apply_shortcut(self, shortcut: str) -> None:
        shortcut_text = shortcut or DEFAULT_CAPTURE_SHORTCUT
        self._shortcut.setKey(QKeySequence(shortcut_text))
        self._shortcut_hint.setText(f"Shortcut: {shortcut_text}")
        self._global_hotkey.start(shortcut_text)

    @Slot()
    def _hide_to_tray(self) -> None:
        if not self._tray.is_available():
            return

        self.hide()
        self._tray.show_hidden_message()

    @Slot()
    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    @Slot()
    def _show_translation_popup(self) -> None:
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    @Slot()
    def _quit_application(self) -> None:
        self._allow_close = True
        self._tray.hide()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._allow_close and self._tray.is_available():
            event.ignore()
            self._hide_to_tray()
            return

        self._global_hotkey.stop()
        self._controller.shutdown()
        super().closeEvent(event)
        QApplication.quit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_press(event):
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_move(event):
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_release(event):
            return

        super().mouseReleaseEvent(event)


def run() -> int:
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(False)
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(run())
