"""Shared visual styling for the RainyOCR PySide UI."""

from __future__ import annotations

from string import Template

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def _build_stylesheet(
    *,
    window_bg: str,
    card_bg: str,
    card_border: str,
    text: str,
    title: str,
    muted: str,
    status_bg: str,
    status_border: str,
    status_text: str,
    secondary_bg: str,
    secondary_border: str,
    secondary_hover: str,
    secondary_pressed: str,
    input_bg: str,
    input_text: str,
    accent: str,
    accent_hover: str,
    primary_end: str,
    primary_hover_end: str,
    primary_text: str,
    selection_text: str,
    scrollbar: str,
    scrollbar_hover: str,
) -> str:
    return Template("""
QMainWindow,
QWidget#translationPopup,
QDialog {
    background-color: $window_bg;
    color: $text;
    font-family: "Noto Sans", "Segoe UI", sans-serif;
    font-size: 14px;
}

QWidget#mainCentral {
    background-color: $window_bg;
}

QFrame#heroCard,
QFrame#translationCard {
    background-color: $card_bg;
    border: 1px solid $card_border;
    border-radius: 22px;
}

QLabel#appTitle,
QLabel#popupTitle,
QLabel#settingsTitle {
    color: $title;
    font-size: 24px;
    font-weight: 700;
}

QLabel#appSubtitle,
QLabel#popupSubtitle,
QLabel#shortcutHint,
QLabel#settingsSubtitle {
    color: $muted;
    font-size: 12px;
}

QLabel#statusLabel {
    background-color: $status_bg;
    border: 1px solid $status_border;
    border-radius: 14px;
    color: $status_text;
    padding: 12px 14px;
}

QPushButton {
    border: none;
    border-radius: 14px;
    color: $text;
    font-size: 14px;
    font-weight: 600;
    min-height: 42px;
    padding: 10px 18px;
}

QPushButton#primaryButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                      stop:0 $accent, stop:1 $primary_end);
    color: $primary_text;
}

QPushButton#primaryButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                      stop:0 $accent_hover, stop:1 $primary_hover_end);
}

QPushButton#primaryButton:pressed {
    background-color: $primary_end;
    padding-top: 12px;
}

QPushButton#secondaryButton {
    background-color: $secondary_bg;
    border: 1px solid $secondary_border;
}

QPushButton#secondaryButton:hover {
    background-color: $secondary_hover;
    border-color: $accent;
}

QPushButton#secondaryButton:pressed {
    background-color: $secondary_pressed;
    padding-top: 12px;
}

QPushButton#settingsGearButton,
QPushButton#themeToggleButton {
    background-color: $secondary_bg;
    border: 1px solid $secondary_border;
    border-radius: 21px;
    color: $text;
    font-size: 20px;
    font-weight: 700;
    min-height: 42px;
    min-width: 42px;
    padding: 0;
}

QPushButton#settingsGearButton:hover,
QPushButton#themeToggleButton:hover {
    background-color: $secondary_hover;
    border-color: $accent;
    color: $title;
}

QPushButton#settingsGearButton:pressed,
QPushButton#themeToggleButton:pressed {
    background-color: $secondary_pressed;
}

QDialog QLabel,
QDialog QGroupBox,
QDialog QGroupBox QLabel {
    color: $text;
}

QLabel#settingsHint {
    color: $muted;
    font-size: 12px;
}

QGroupBox#settingsGroup {
    background-color: $card_bg;
    border: 1px solid $card_border;
    border-radius: 18px;
    color: $status_text;
    font-weight: 700;
    margin-top: 12px;
}

QGroupBox#settingsGroup::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
}

QLineEdit,
QKeySequenceEdit,
QSpinBox {
    background-color: $input_bg;
    border: 1px solid $card_border;
    border-radius: 12px;
    color: $input_text;
    min-height: 34px;
    padding: 6px 10px;
    selection-background-color: $accent;
    selection-color: $selection_text;
}

QLineEdit:focus,
QKeySequenceEdit:focus,
QSpinBox:focus {
    border-color: $accent;
}

QDialogButtonBox QPushButton {
    min-width: 96px;
}

QTextEdit#translationText {
    background-color: $input_bg;
    border: 1px solid $card_border;
    border-radius: 18px;
    color: $input_text;
    font-size: 15px;
    padding: 14px;
    selection-background-color: $accent;
    selection-color: $selection_text;
}

QScrollBar:vertical {
    background: transparent;
    margin: 10px 4px 10px 0;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: $scrollbar;
    border-radius: 5px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: $scrollbar_hover;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
""").substitute(
        window_bg=window_bg,
        card_bg=card_bg,
        card_border=card_border,
        text=text,
        title=title,
        muted=muted,
        status_bg=status_bg,
        status_border=status_border,
        status_text=status_text,
        secondary_bg=secondary_bg,
        secondary_border=secondary_border,
        secondary_hover=secondary_hover,
        secondary_pressed=secondary_pressed,
        input_bg=input_bg,
        input_text=input_text,
        accent=accent,
        accent_hover=accent_hover,
        primary_end=primary_end,
        primary_hover_end=primary_hover_end,
        primary_text=primary_text,
        selection_text=selection_text,
        scrollbar=scrollbar,
        scrollbar_hover=scrollbar_hover,
    )


DARK_STYLESHEET = _build_stylesheet(
    window_bg="#101820",
    card_bg="#172431",
    card_border="#2b536d",
    text="#e7eef7",
    title="#f7fbff",
    muted="#8fa6ba",
    status_bg="#1a3347",
    status_border="#2c5978",
    status_text="#cfe9ff",
    secondary_bg="#223142",
    secondary_border="#3a5063",
    secondary_hover="#2a3d51",
    secondary_pressed="#24465c",
    input_bg="#0d141c",
    input_text="#edf7ff",
    accent="#35d2ff",
    accent_hover="#61dcff",
    primary_end="#3f83ff",
    primary_hover_end="#64a0ff",
    primary_text="#06121f",
    selection_text="#07131d",
    scrollbar="#50677a",
    scrollbar_hover="#75cbff",
)

LIGHT_STYLESHEET = _build_stylesheet(
    window_bg="#edf7fb",
    card_bg="#ffffff",
    card_border="#b8d8e6",
    text="#163040",
    title="#0b2232",
    muted="#607988",
    status_bg="#dff3fb",
    status_border="#aad8eb",
    status_text="#164157",
    secondary_bg="#e5f1f6",
    secondary_border="#b7cfda",
    secondary_hover="#d6edf6",
    secondary_pressed="#c3e2ef",
    input_bg="#f8fcff",
    input_text="#102b3b",
    accent="#19a8d8",
    accent_hover="#37bde9",
    primary_end="#5b9cff",
    primary_hover_end="#78adff",
    primary_text="#ffffff",
    selection_text="#ffffff",
    scrollbar="#9eb8c5",
    scrollbar_hover="#4ebfe7",
)

APP_STYLESHEET = LIGHT_STYLESHEET


def stylesheet_for_theme(is_dark: bool) -> str:
    return DARK_STYLESHEET if is_dark else LIGHT_STYLESHEET


def add_soft_shadow(widget: QWidget) -> None:
    """Apply a restrained drop shadow to card-like widgets."""

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(32)
    shadow.setXOffset(0)
    shadow.setYOffset(14)
    shadow.setColor(QColor(0, 0, 0, 95))
    widget.setGraphicsEffect(shadow)
