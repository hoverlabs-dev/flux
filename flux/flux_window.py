from __future__ import annotations

import os
import math
import subprocess
from datetime import datetime
from pathlib import Path

# pyrefly: ignore [missing-import]
from PyQt6 import QtCore, QtGui, QtWidgets

from bridge_core.settings import PROJECT_ROOT
from bridge_core.license_manager import check_license, verify_gumroad_license, get_hardware_id
from .config import FluxConfig
from .dcc_commands import blender_bootstrap_expr, bridge_action_code, maya_bootstrap_command
from .styles import DARK_NEON_QSS
from .transport import send_python


class AnimatedButton(QtWidgets.QPushButton):
    def __init__(self, label: str, primary: bool = False, parent=None):
        self._is_primary = primary
        super().__init__(label, parent)
        
        # Initialize default colors based on primary or ghost button styles
        if self._is_primary:
            self._bg_color = QtGui.QColor("#ffffff")
            self._border_color = QtGui.QColor("#ffffff")
            self._text_color = QtGui.QColor("#000000")
        else:
            self._bg_color = QtGui.QColor(0, 0, 0, 0)
            self._border_color = QtGui.QColor("#1f1f1f")
            self._text_color = QtGui.QColor("#ffffff")
            
        # Set static stylesheet once to setup padding, border removal, font weight, etc.
        font_weight = "700" if self._is_primary else "500"
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {self._text_color.name()};
                font-weight: {font_weight};
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: transparent;
                border: none;
                color: {self._text_color.name()};
                padding: 6px 12px;
            }}
            QPushButton:pressed {{
                background: transparent;
                border: none;
                color: {self._text_color.name()};
                padding: 6px 12px;
            }}
        """)
            
        # Glow graphics effect
        self.glow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(15 if self._is_primary else 0)
        self.glow.setXOffset(0)
        self.glow.setYOffset(0)
        self.glow.setColor(QtGui.QColor(255, 255, 255, 100) if self._is_primary else QtGui.QColor(255, 255, 255, 40))
        self.glow.setEnabled(True if self._is_primary else False)
        self.setGraphicsEffect(self.glow)
        
        # Setup property animations
        self.bg_anim = QtCore.QPropertyAnimation(self, b"bgColor")
        self.bg_anim.setDuration(150)
        self.bg_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.border_anim = QtCore.QPropertyAnimation(self, b"borderColor")
        self.border_anim.setDuration(150)
        self.border_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.glow_anim = QtCore.QPropertyAnimation(self.glow, b"blurRadius")
        self.glow_anim.setDuration(150)
        self.glow_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.group = QtCore.QParallelAnimationGroup()
        self.group.addAnimation(self.bg_anim)
        self.group.addAnimation(self.border_anim)
        self.group.addAnimation(self.glow_anim)
        
        self.group.finished.connect(self._on_anim_finished)
        
    def getBgColor(self) -> QtGui.QColor:
        return self._bg_color
    def setBgColor(self, color: QtGui.QColor):
        self._bg_color = color
        self.update()
        
    def getBorderColor(self) -> QtGui.QColor:
        return self._border_color
    def setBorderColor(self, color: QtGui.QColor):
        self._border_color = color
        self.update()
        
    bgColor = QtCore.pyqtProperty(QtGui.QColor, getBgColor, setBgColor)
    borderColor = QtCore.pyqtProperty(QtGui.QColor, getBorderColor, setBorderColor)
    
    def _on_anim_finished(self):
        if not self.underMouse() and not self._is_primary:
            self.glow.setEnabled(False)
            
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(self._bg_color))
            painter.setPen(QtGui.QPen(self._border_color, 1.0))
            rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            painter.drawRoundedRect(rect, 6.0, 6.0)
        finally:
            painter.end()
        super().paintEvent(event)
        
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        self.group.stop()
        if not self._is_primary:
            self.glow.setEnabled(True)
        
        # Target colors on hover
        if self._is_primary:
            target_bg = QtGui.QColor("#ececec")
            target_border = QtGui.QColor("#ececec")
            target_glow = 25
        else:
            target_bg = QtGui.QColor("#1a1a1a")
            target_border = QtGui.QColor("#555555")
            target_glow = 12
            
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(target_bg)
        
        self.border_anim.setStartValue(self._border_color)
        self.border_anim.setEndValue(target_border)
        
        self.glow_anim.setStartValue(self.glow.blurRadius())
        self.glow_anim.setEndValue(target_glow)
        
        self.group.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.group.stop()
        
        # Target colors on restore
        if self._is_primary:
            target_bg = QtGui.QColor("#ffffff")
            target_border = QtGui.QColor("#ffffff")
            target_glow = 15
        else:
            target_bg = QtGui.QColor(0, 0, 0, 0)
            target_border = QtGui.QColor("#1f1f1f")
            target_glow = 0
            
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(target_bg)
        
        self.border_anim.setStartValue(self._border_color)
        self.border_anim.setEndValue(target_border)
        
        self.glow_anim.setStartValue(self.glow.blurRadius())
        self.glow_anim.setEndValue(target_glow)
        
        self.group.start()
        super().leaveEvent(event)


class AnimatedNavButton(QtWidgets.QPushButton):
    def __init__(self, label: str, active: bool = False, parent=None):
        super().__init__(label, parent)
        self._active = active
        
        # Initialize default colors
        if self._active:
            self._bg_color = QtGui.QColor("#1f1f1f")
            self._border_color = QtGui.QColor("#2e2e2e")
            self._text_color = QtGui.QColor("#ffffff")
        else:
            self._bg_color = QtGui.QColor(0, 0, 0, 0)
            self._border_color = QtGui.QColor(0, 0, 0, 0)
            self._text_color = QtGui.QColor("#888888")
            
        # Set static stylesheet once to setup padding, border removal, font weight, etc.
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 6px 14px;
                min-height: 24px;
            }
            QPushButton:hover {
                background: transparent;
                border: none;
                padding: 6px 14px;
            }
            QPushButton:pressed {
                background: transparent;
                border: none;
                padding: 6px 14px;
            }
        """)
        
        # Setup property animations
        self.bg_anim = QtCore.QPropertyAnimation(self, b"bgColor")
        self.bg_anim.setDuration(150)
        self.bg_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.border_anim = QtCore.QPropertyAnimation(self, b"borderColor")
        self.border_anim.setDuration(150)
        self.border_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.text_anim = QtCore.QPropertyAnimation(self, b"textColor")
        self.text_anim.setDuration(150)
        self.text_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.group = QtCore.QParallelAnimationGroup()
        self.group.addAnimation(self.bg_anim)
        self.group.addAnimation(self.border_anim)
        self.group.addAnimation(self.text_anim)
        
        self._update_palette()
        
    def getBgColor(self) -> QtGui.QColor:
        return self._bg_color
    def setBgColor(self, color: QtGui.QColor):
        self._bg_color = color
        self.update()
        
    def getBorderColor(self) -> QtGui.QColor:
        return self._border_color
    def setBorderColor(self, color: QtGui.QColor):
        self._border_color = color
        self.update()
        
    def getTextColor(self) -> QtGui.QColor:
        return self._text_color
    def setTextColor(self, color: QtGui.QColor):
        self._text_color = color
        self._update_palette()
        
    bgColor = QtCore.pyqtProperty(QtGui.QColor, getBgColor, setBgColor)
    borderColor = QtCore.pyqtProperty(QtGui.QColor, getBorderColor, setBorderColor)
    textColor = QtCore.pyqtProperty(QtGui.QColor, getTextColor, setTextColor)
    
    def _update_palette(self):
        palette = self.palette()
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, self._text_color)
        self.setPalette(palette)
        self.update()
        
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(self._bg_color))
            painter.setPen(QtGui.QPen(self._border_color, 1.0))
            rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            painter.drawRoundedRect(rect, 6.0, 6.0)
        finally:
            painter.end()
        super().paintEvent(event)
        
    def set_active(self, active: bool):
        self._active = active
        self.group.stop()
        
        if active:
            target_bg = QtGui.QColor("#1f1f1f")
            target_border = QtGui.QColor("#2e2e2e")
            target_text = QtGui.QColor("#ffffff")
        else:
            target_bg = QtGui.QColor(0, 0, 0, 0)
            target_border = QtGui.QColor(0, 0, 0, 0)
            target_text = QtGui.QColor("#888888")
            
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(target_bg)
        self.border_anim.setStartValue(self._border_color)
        self.border_anim.setEndValue(target_border)
        self.text_anim.setStartValue(self._text_color)
        self.text_anim.setEndValue(target_text)
        self.group.start()
        
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if not self._active:
            self.group.stop()
            self.bg_anim.setStartValue(self._bg_color)
            self.bg_anim.setEndValue(QtGui.QColor("#141414"))
            self.border_anim.setStartValue(self._border_color)
            self.border_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.text_anim.setStartValue(self._text_color)
            self.text_anim.setEndValue(QtGui.QColor("#ffffff"))
            self.group.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if not self._active:
            self.group.stop()
            self.bg_anim.setStartValue(self._bg_color)
            self.bg_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.border_anim.setStartValue(self._border_color)
            self.border_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.text_anim.setStartValue(self._text_color)
            self.text_anim.setEndValue(QtGui.QColor("#888888"))
            self.group.start()
        super().leaveEvent(event)


class AnimatedSegmentButton(QtWidgets.QPushButton):
    def __init__(self, label: str, active: bool = False, parent=None):
        super().__init__(label, parent)
        self._active = active
        
        # Initialize default colors
        if self._active:
            self._bg_color = QtGui.QColor("#1f1f1f")
            self._border_color = QtGui.QColor("#2e2e2e")
            self._text_color = QtGui.QColor("#ffffff")
        else:
            self._bg_color = QtGui.QColor(0, 0, 0, 0)
            self._border_color = QtGui.QColor(0, 0, 0, 0)
            self._text_color = QtGui.QColor("#888888")
            
        # Set static stylesheet once to setup padding, border removal, font weight, etc.
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 8px 16px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: transparent;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:pressed {
                background: transparent;
                border: none;
                padding: 8px 16px;
            }
        """)
        
        # Setup property animations
        self.bg_anim = QtCore.QPropertyAnimation(self, b"bgColor")
        self.bg_anim.setDuration(150)
        self.bg_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.border_anim = QtCore.QPropertyAnimation(self, b"borderColor")
        self.border_anim.setDuration(150)
        self.border_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.text_anim = QtCore.QPropertyAnimation(self, b"textColor")
        self.text_anim.setDuration(150)
        self.text_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        self.group = QtCore.QParallelAnimationGroup()
        self.group.addAnimation(self.bg_anim)
        self.group.addAnimation(self.border_anim)
        self.group.addAnimation(self.text_anim)
        
        self._update_palette()
        
    def getBgColor(self) -> QtGui.QColor:
        return self._bg_color
    def setBgColor(self, color: QtGui.QColor):
        self._bg_color = color
        self.update()
        
    def getBorderColor(self) -> QtGui.QColor:
        return self._border_color
    def setBorderColor(self, color: QtGui.QColor):
        self._border_color = color
        self.update()
        
    def getTextColor(self) -> QtGui.QColor:
        return self._text_color
    def setTextColor(self, color: QtGui.QColor):
        self._text_color = color
        self._update_palette()
        
    bgColor = QtCore.pyqtProperty(QtGui.QColor, getBgColor, setBgColor)
    borderColor = QtCore.pyqtProperty(QtGui.QColor, getBorderColor, setBorderColor)
    textColor = QtCore.pyqtProperty(QtGui.QColor, getTextColor, setTextColor)
    
    def _update_palette(self):
        palette = self.palette()
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, self._text_color)
        self.setPalette(palette)
        self.update()
        
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(self._bg_color))
            painter.setPen(QtGui.QPen(self._border_color, 1.0))
            rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            painter.drawRoundedRect(rect, 6.0, 6.0)
        finally:
            painter.end()
        super().paintEvent(event)
        
    def set_active(self, active: bool):
        self._active = active
        self.group.stop()
        
        if active:
            target_bg = QtGui.QColor("#1f1f1f")
            target_border = QtGui.QColor("#2e2e2e")
            target_text = QtGui.QColor("#ffffff")
        else:
            target_bg = QtGui.QColor(0, 0, 0, 0)
            target_border = QtGui.QColor(0, 0, 0, 0)
            target_text = QtGui.QColor("#888888")
            
        self.bg_anim.setStartValue(self._bg_color)
        self.bg_anim.setEndValue(target_bg)
        self.border_anim.setStartValue(self._border_color)
        self.border_anim.setEndValue(target_border)
        self.text_anim.setStartValue(self._text_color)
        self.text_anim.setEndValue(target_text)
        self.group.start()
        
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if not self._active:
            self.group.stop()
            self.bg_anim.setStartValue(self._bg_color)
            self.bg_anim.setEndValue(QtGui.QColor("#141414"))
            self.border_anim.setStartValue(self._border_color)
            self.border_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.text_anim.setStartValue(self._text_color)
            self.text_anim.setEndValue(QtGui.QColor("#ffffff"))
            self.group.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if not self._active:
            self.group.stop()
            self.bg_anim.setStartValue(self._bg_color)
            self.bg_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.border_anim.setStartValue(self._border_color)
            self.border_anim.setEndValue(QtGui.QColor(0, 0, 0, 0))
            self.text_anim.setStartValue(self._text_color)
            self.text_anim.setEndValue(QtGui.QColor("#888888"))
            self.group.start()
        super().leaveEvent(event)


class AnimatedDot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._color = QtGui.QColor("#333333")
        self._glow_alpha = 0.0
        
    def getColor(self) -> QtGui.QColor:
        return self._color
    def setColor(self, color: QtGui.QColor):
        self._color = color
        self.update()
        
    def getGlowAlpha(self) -> float:
        return self._glow_alpha
    def setGlowAlpha(self, val: float):
        self._glow_alpha = val
        self.update()
        
    color = QtCore.pyqtProperty(QtGui.QColor, getColor, setColor)
    glowAlpha = QtCore.pyqtProperty(float, getGlowAlpha, setGlowAlpha)
    
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            if self._glow_alpha > 0:
                grad = QtGui.QRadialGradient(8, 8, 8)
                grad.setColorAt(0.0, QtGui.QColor(16, 185, 129, int(self._glow_alpha)))
                grad.setColorAt(0.4, QtGui.QColor(16, 185, 129, int(self._glow_alpha * 0.6)))
                grad.setColorAt(1.0, QtGui.QColor(16, 185, 129, 0))
                painter.setBrush(QtGui.QBrush(grad))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawEllipse(0, 0, 16, 16)
            painter.setBrush(QtGui.QBrush(self._color))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            # Draw 6x6 ellipse in the center of 16x16 widget
            painter.drawEllipse(5, 5, 6, 6)
        finally:
            painter.end()
        
    def set_active(self, active: bool, animate: bool = True):
        target_color = QtGui.QColor("#10b981") if active else QtGui.QColor("#333333")
        target_glow = 180.0 if active else 0.0
        if not animate:
            self._color = target_color
            self._glow_alpha = target_glow
            self.update()
            return
            
        self.color_anim = QtCore.QPropertyAnimation(self, b"color")
        self.color_anim.setDuration(300)
        self.color_anim.setStartValue(self._color)
        self.color_anim.setEndValue(target_color)
        
        self.glow_anim = QtCore.QPropertyAnimation(self, b"glowAlpha")
        self.glow_anim.setDuration(300)
        self.glow_anim.setStartValue(self._glow_alpha)
        self.glow_anim.setEndValue(target_glow)
        
        self.group = QtCore.QParallelAnimationGroup()
        self.group.addAnimation(self.color_anim)
        self.group.addAnimation(self.glow_anim)
        self.group.start()


class WordWrapCheckBox(QtWidgets.QWidget):
    stateChanged = QtCore.pyqtSignal(int)
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.checkbox = QtWidgets.QCheckBox()
        self.label = QtWidgets.QLabel(text)
        self.label.setWordWrap(True)
        
        self.checkbox.setStyleSheet("QCheckBox { spacing: 0px; }")
        
        self.setObjectName("WordWrapCheckBox")
        self.setStyleSheet("""
            #WordWrapCheckBox QLabel {
                color: #888888;
                font-size: 8pt;
                font-family: "Geist", Menlo, Monaco, Consolas, "Courier New", monospace;
            }
            #WordWrapCheckBox:hover QLabel {
                color: #ffffff;
            }
            #WordWrapCheckBox QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #333333;
                background-color: #000000;
            }
            #WordWrapCheckBox:hover QCheckBox::indicator {
                border: 1px solid #444444;
            }
            #WordWrapCheckBox QCheckBox::indicator:checked {
                border: 1px solid #ffffff;
                background-color: #ffffff;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.checkbox, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label, 1)
        
        self.checkbox.stateChanged.connect(self.stateChanged.emit)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        
    def isChecked(self) -> bool:
        return self.checkbox.isChecked()
        
    def setChecked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)
        
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.checkbox.toggle()
        super().mousePressEvent(event)
        
    def setToolTip(self, text: str) -> None:
        super().setToolTip(text)
        self.checkbox.setToolTip(text)
        self.label.setToolTip(text)

    def sizeHint(self) -> QtCore.QSize:
        lbl_hint = self.label.sizeHint()
        return QtCore.QSize(lbl_hint.width() + 22, max(18, lbl_hint.height()))

    def minimumSizeHint(self) -> QtCore.QSize:
        return self.sizeHint()


class HoverIconButton(QtWidgets.QPushButton):
    def __init__(self, icon_name: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setFixedSize(16, 16)
        self.window = None
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
    def set_window(self, win):
        self.window = win
        self.setIcon(self.window.create_vector_icon(self.icon_name, "#888888"))
        self.setIconSize(QtCore.QSize(16, 16))
        
    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        if self.window:
            self.setIcon(self.window.create_vector_icon(self.icon_name, "#ffffff"))
        super().enterEvent(event)
        
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if self.window:
            self.setIcon(self.window.create_vector_icon(self.icon_name, "#888888"))
        super().leaveEvent(event)


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Flux")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.resize(320, 240)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        container = QtWidgets.QWidget()
        container.setObjectName("AboutContainer")
        container.setStyleSheet("""
            QWidget#AboutContainer {
                background-color: #0c0c0c;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
            QLabel {
                color: #888888;
                font-family: "Geist Mono", "Segoe UI", Arial;
            }
            QLabel#AboutTitle {
                color: #ffffff;
                font-size: 12pt;
                font-weight: 700;
            }
            QLabel#AboutHighlight {
                color: #a3a3a3;
                font-size: 9pt;
            }
        """)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(18, 18, 18, 18)
        container_layout.setSpacing(10)
        
        title = QtWidgets.QLabel("F L U X")
        title.setObjectName("AboutTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        desc = QtWidgets.QLabel("Maya ↔ Blender Asset Bridge\nHigh-performance local asset roundtrips via FBX.")
        desc.setObjectName("AboutHighlight")
        desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        
        info_form = QtWidgets.QFormLayout()
        info_form.setContentsMargins(0, 8, 0, 8)
        info_form.setSpacing(6)
        
        def add_info_row(label: str, val: str):
            lbl = QtWidgets.QLabel(label)
            lbl.setStyleSheet("font-weight: 600; color: #555555; font-size: 8.5pt;")
            v = QtWidgets.QLabel(val)
            v.setStyleSheet("color: #a3a3a3; font-size: 8.5pt;")
            info_form.addRow(lbl, v)
            
        add_info_row("Version", "v1.0.0")
        add_info_row("Year", "2026")
        add_info_row("Developer", "Jaisurya C | Tech Art")
        #add_info_row("License", "MIT License")
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setObjectName("GhostBtn")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #1f1f1f;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 12px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #161616;
                border: 1px solid #444444;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        container_layout.addWidget(title)
        container_layout.addWidget(desc)
        container_layout.addLayout(info_form)
        container_layout.addWidget(close_btn, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(container)
        
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()


class FluxWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = FluxConfig.load()
        self.direction = "maya"
        self.setWindowTitle("Flux - Maya Blender Asset Bridge (FBX)")
        self.resize(450, 520)
        self.setMinimumSize(420, 420)
        
        # Frameless rounded window settings
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint | 
            QtCore.Qt.WindowType.Window | 
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Load custom bundled fonts
        geist_path = PROJECT_ROOT / "icons" / "Geist.ttf"
        if geist_path.exists():
            QtGui.QFontDatabase.addApplicationFont(str(geist_path))
            
        geist_mono_path = PROJECT_ROOT / "icons" / "GeistMono.ttf"
        if geist_mono_path.exists():
            QtGui.QFontDatabase.addApplicationFont(str(geist_mono_path))
            
        self.setStyleSheet(DARK_NEON_QSS)
        
        # Set gorgeous branded window icon
        flux_icon_path = PROJECT_ROOT / "icons" / "flux_logo.png"
        if flux_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(flux_icon_path)))
        else:
            window_icon = self.create_vector_icon("maya")
            if window_icon:
                self.setWindowIcon(window_icon)
            
        self._build_ui()
        self._load_config_to_ui()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def create_vector_icon(self, name: str, color_hex: str = "#ffffff") -> QtGui.QIcon:
        """Dynamically draws or loads pixel-perfect high-resolution icons."""
        if name == "maya":
            icon_path = PROJECT_ROOT / "icons" / "maya_logo.png"
            if icon_path.exists():
                return QtGui.QIcon(str(icon_path))
        elif name == "blender":
            icon_path = PROJECT_ROOT / "icons" / "blender_icon.png"
            if icon_path.exists():
                return QtGui.QIcon(str(icon_path))

        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        
        color = QtGui.QColor(color_hex)
        pen = QtGui.QPen(color, 2.5, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        if name == "maya":
            path = QtGui.QPainterPath()
            path.moveTo(6, 26)
            path.lineTo(6, 8)
            path.lineTo(16, 20)
            path.lineTo(26, 8)
            path.lineTo(26, 26)
            painter.drawPath(path)
        elif name == "blender":
            painter.drawEllipse(11, 11, 10, 10)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawEllipse(14, 14, 4, 4)
            painter.setBrush(QtGui.QBrush(QtCore.Qt.GlobalColor.transparent))
            painter.drawLine(16, 7, 24, 7)
            painter.drawLine(16, 7, 16, 11)
            painter.drawLine(21, 21, 26, 26)
        elif name == "export":
            painter.drawRect(8, 12, 16, 14)
            path = QtGui.QPainterPath()
            path.moveTo(16, 16)
            path.lineTo(16, 4)
            path.moveTo(11, 9)
            path.lineTo(16, 4)
            path.lineTo(21, 9)
            painter.drawPath(path)
        elif name == "import":
            painter.drawRect(8, 12, 16, 14)
            path = QtGui.QPainterPath()
            path.moveTo(16, 4)
            path.lineTo(16, 16)
            path.moveTo(11, 11)
            path.lineTo(16, 16)
            path.lineTo(21, 11)
            painter.drawPath(path)
        elif name == "sync":
            painter.drawArc(6, 6, 20, 20, 30 * 16, 270 * 16)
            painter.drawLine(23, 11, 23, 6)
            painter.drawLine(23, 6, 18, 6)
            
            painter.drawArc(6, 6, 20, 20, 210 * 16, 270 * 16)
            painter.drawLine(9, 21, 9, 26)
            painter.drawLine(9, 26, 14, 26)
        elif name == "folder":
            path = QtGui.QPainterPath()
            path.moveTo(6, 26)
            path.lineTo(6, 8)
            path.lineTo(13, 8)
            path.lineTo(16, 12)
            path.lineTo(26, 12)
            path.lineTo(26, 26)
            path.closeSubpath()
            painter.drawPath(path)
        elif name == "settings":
            painter.drawEllipse(11, 11, 10, 10)
            for i in range(8):
                angle = i * 45
                rad = angle * math.pi / 180.0
                x1 = 16 + 10 * math.cos(rad)
                y1 = 16 + 10 * math.sin(rad)
                x2 = 16 + 13 * math.cos(rad)
                y2 = 16 + 13 * math.sin(rad)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        elif name == "policy":
            path = QtGui.QPainterPath()
            path.moveTo(16, 6)
            path.lineTo(26, 8)
            path.lineTo(26, 17)
            path.quadTo(26, 23, 16, 27)
            path.quadTo(6, 23, 6, 17)
            path.lineTo(6, 8)
            path.closeSubpath()
            painter.drawPath(path)
        elif name == "bolt":
            path = QtGui.QPainterPath()
            path.moveTo(18, 4)
            path.lineTo(8, 16)
            path.lineTo(15, 16)
            path.lineTo(14, 28)
            path.lineTo(24, 16)
            path.lineTo(17, 16)
            path.closeSubpath()
            painter.drawPath(path)
        elif name == "info":
            painter.drawEllipse(7, 7, 18, 18)
            painter.drawLine(16, 15, 16, 21)
            painter.fillRect(15, 11, 2, 2, color)
            
        painter.end()
        return QtGui.QIcon(pixmap)

    def _set_dot_state(self, dot: AnimatedDot, is_active: bool) -> None:
        dot.set_active(is_active)

    def _animate_toggle_widget(self, widget: QtWidgets.QWidget, show: bool, default_target_height: int = -1):
        if not hasattr(self, "_active_animations"):
            self._active_animations = {}
            
        # Stop any existing animation group for this widget
        if widget in self._active_animations:
            self._active_animations[widget].stop()
            
        # Setup opacity effect
        eff = widget.graphicsEffect()
        if not isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
            eff = QtWidgets.QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(eff)
            
        # Determine the target height of the widget
        if show:
            widget.setVisible(True)
            if default_target_height > 0:
                target_widget_height = default_target_height
            else:
                widget.setMaximumHeight(16777215)
                widget.adjustSize()
                target_widget_height = widget.sizeHint().height()
            
            # Start height should be current height or 0 if it was hidden
            current_widget_height = widget.height() if widget.isVisible() and widget.maximumHeight() < 16777215 else 0
        else:
            target_widget_height = 0
            current_widget_height = widget.height()
            
        current_window_geom = self.geometry()
        
        # Calculate target window height
        height_diff = target_widget_height - current_widget_height
        target_window_height = current_window_geom.height() + height_diff
        
        # Prevent window from shrinking below minimum size
        if target_window_height < self.minimumHeight():
            target_window_height = self.minimumHeight()
            
        target_window_geom = QtCore.QRect(
            current_window_geom.x(),
            current_window_geom.y(),
            current_window_geom.width(),
            target_window_height
        )
        
        # Create animations
        # 1. Widget height animation
        height_anim = QtCore.QPropertyAnimation(widget, b"maximumHeight")
        height_anim.setDuration(220)
        height_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        height_anim.setStartValue(current_widget_height)
        height_anim.setEndValue(target_widget_height)
        
        # 2. Widget opacity animation
        opacity_anim = QtCore.QPropertyAnimation(eff, b"opacity")
        opacity_anim.setDuration(220)
        opacity_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        opacity_anim.setStartValue(eff.opacity() if show else 1.0)
        opacity_anim.setEndValue(1.0 if show else 0.0)
        
        # 3. Main window geometry animation
        window_anim = QtCore.QPropertyAnimation(self, b"geometry")
        window_anim.setDuration(220)
        window_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        window_anim.setStartValue(current_window_geom)
        window_anim.setEndValue(target_window_geom)
        
        # Parallel group
        group = QtCore.QParallelAnimationGroup(self)
        group.addAnimation(height_anim)
        group.addAnimation(opacity_anim)
        group.addAnimation(window_anim)
        
        def on_finished():
            if not show:
                widget.setVisible(False)
            widget.setGraphicsEffect(None) # Remove opacity effect to restore standard painting!
            if widget in self._active_animations:
                self._active_animations.pop(widget, None)
                
        group.finished.connect(on_finished)
        self._active_animations[widget] = group
        group.start()

    def _fade_switch_page(self, index: int) -> None:
        if self.central_stack.currentIndex() == index:
            return
            
        # Get or create graphics opacity effect on central_stack
        eff = self.central_stack.graphicsEffect()
        if not isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
            eff = QtWidgets.QGraphicsOpacityEffect(self.central_stack)
            self.central_stack.setGraphicsEffect(eff)
            
        # Stop any running animation on this effect
        if hasattr(self, "_fade_anim") and self._fade_anim.state() == QtCore.QAbstractAnimation.State.Running:
            self._fade_anim.stop()
            
        # Fade out
        self._fade_anim = QtCore.QPropertyAnimation(eff, b"opacity")
        self._fade_anim.setDuration(80)
        self._fade_anim.setStartValue(eff.opacity() if eff.opacity() > 0 else 1.0)
        self._fade_anim.setEndValue(0.0)
        
        def on_fade_out_finished():
            # Update size policies so inactive page sizeHint doesn't override active page sizeHint
            for i in range(self.central_stack.count()):
                page = self.central_stack.widget(i)
                if i == index:
                    page.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
                else:
                    page.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Ignored)
            
            self.central_stack.setCurrentIndex(index)
            self.central_stack.adjustSize()
            
            # Adjust window size if needed
            QtCore.QTimer.singleShot(10, self._animate_window_to_size)
            
            # Fade in
            self._fade_anim_in = QtCore.QPropertyAnimation(eff, b"opacity")
            self._fade_anim_in.setDuration(100)
            self._fade_anim_in.setStartValue(0.0)
            self._fade_anim_in.setEndValue(1.0)
            
            def on_fade_in_finished():
                self.central_stack.setGraphicsEffect(None) # Remove opacity effect after fade-in!
                
            self._fade_anim_in.finished.connect(on_fade_in_finished)
            self._fade_anim_in.start()
            
        self._fade_anim.finished.connect(on_fade_out_finished)
        self._fade_anim.start()

    def _animate_window_to_size(self) -> None:
        if hasattr(self, "_window_size_anim") and self._window_size_anim.state() == QtCore.QAbstractAnimation.State.Running:
            self._window_size_anim.stop()
            
        current_geom = self.geometry()
        # Force layout update to ensure sizeHint is accurate for the new page layout
        target_height = self.sizeHint().height()
        
        if target_height < self.minimumHeight():
            target_height = self.minimumHeight()
            
        target_geom = QtCore.QRect(
            current_geom.x(),
            current_geom.y(),
            current_geom.width(),
            target_height
        )
        
        self._window_size_anim = QtCore.QPropertyAnimation(self, b"geometry")
        self._window_size_anim.setDuration(200)
        self._window_size_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._window_size_anim.setStartValue(current_geom)
        self._window_size_anim.setEndValue(target_geom)
        self._window_size_anim.start()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(18, 0, 18, 18)
        root.setSpacing(12)

        # Title Bar (Frameless dragging area)
        title_bar = QtWidgets.QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar_layout = QtWidgets.QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(8, 0, 8, 0)
        title_bar_layout.setSpacing(8)
        
        self.close_dot = QtWidgets.QPushButton()
        self.close_dot.setFixedSize(12, 12)
        self.close_dot.setObjectName("CloseDot")
        self.close_dot.setToolTip("Close Window")
        self.close_dot.clicked.connect(self.close)
        
        self.min_dot = QtWidgets.QPushButton()
        self.min_dot.setFixedSize(12, 12)
        self.min_dot.setObjectName("MinDot")
        self.min_dot.setToolTip("Minimize Window")
        self.min_dot.clicked.connect(self.showMinimized)
        
        title_lbl = QtWidgets.QLabel("F L U X")
        title_lbl.setObjectName("TitleBarTitle")
        title_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        notch_shadow = QtWidgets.QGraphicsDropShadowEffect(title_lbl)
        notch_shadow.setBlurRadius(100)
        notch_shadow.setXOffset(0)
        notch_shadow.setYOffset(3)
        notch_shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        title_lbl.setGraphicsEffect(notch_shadow)
        
        self.info_btn = HoverIconButton("info", self)
        self.info_btn.setObjectName("InfoBtn")
        self.info_btn.set_window(self)
        self.info_btn.setToolTip("About Flux")
        self.info_btn.clicked.connect(self.show_about_dialog)
        
        right_spacer = QtWidgets.QWidget()
        right_spacer.setFixedSize(16, 12)
        
        title_bar_layout.addWidget(self.close_dot, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        title_bar_layout.addWidget(self.min_dot, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(title_lbl, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(self.info_btn, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        title_bar_layout.addWidget(right_spacer, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        root.addWidget(title_bar)

        # 1. Header Navigation
        root.addLayout(self._header())

        # Vercel navigation switcher
        nav_container = QtWidgets.QWidget()
        nav_container.setObjectName("NavContainer")
        nav_layout = QtWidgets.QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(2, 2, 2, 2)
        nav_layout.setSpacing(2)
        
        self.nav_terminal_btn = AnimatedNavButton("Terminal", active=True)
        self.nav_terminal_btn.setToolTip("Terminal controls for launching DCCs and running sync actions")
        self.nav_terminal_btn.clicked.connect(self._show_terminal_page)
        
        self.nav_settings_btn = AnimatedNavButton("Settings", active=False)
        self.nav_settings_btn.setToolTip("Application preferences, executable paths, and port configurations")
        self.nav_settings_btn.clicked.connect(self._show_settings_page)
        
        nav_layout.addWidget(self.nav_terminal_btn, 1)
        nav_layout.addWidget(self.nav_settings_btn, 1)
        
        root.addWidget(nav_container)

        # 2. Main Stacked page views
        self.central_stack = QtWidgets.QStackedWidget()
        
        self._build_license_page()
        self._build_terminal_page()
        self._build_config_page()
        
        self.central_stack.addWidget(self.license_page)
        self.central_stack.addWidget(self.terminal_page)
        self.central_stack.addWidget(self.config_page)
        
        root.addWidget(self.central_stack, 1)

        is_activated = check_license(self.config.license_key, self.config.cached_hwid)
        if is_activated:
            self._show_terminal_page()
        else:
            self._show_license_page()

    def _build_license_page(self) -> None:
        self.license_page = QtWidgets.QWidget()
        self.license_page.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        layout = QtWidgets.QVBoxLayout(self.license_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        card = QtWidgets.QFrame()
        card.setObjectName("ControlHubFrame")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        title = QtWidgets.QLabel("Product Activation")
        title.setStyleSheet("color: #ffffff; font-size: 11pt; font-weight: 700;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        info = QtWidgets.QLabel(
            "Flux Indie license allows validation on up to 2 creative systems.\n"
            "Please enter the product license key from your Gumroad purchase receipt."
        )
        info.setStyleSheet("color: #888888; font-size: 8.5pt; line-height: 1.4;")
        info.setWordWrap(True)
        info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.license_input = QtWidgets.QLineEdit()
        self.license_input.setPlaceholderText("Paste your license key here (e.g. XXXX-XXXX-...)")
        self.license_input.setMinimumHeight(32)
        
        self.activate_btn = self._button("Activate License", self._on_activate_clicked, primary=True)
        self.activate_btn.setMinimumHeight(36)

        self.license_status = QtWidgets.QLabel("")
        self.license_status.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #ef4444;")
        self.license_status.setWordWrap(True)
        self.license_status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        buy_lbl = QtWidgets.QLabel(
            "<a href='https://gumroad.com' style='color: #2563eb; text-decoration: none; font-weight: 600;'>Buy Flux License on Gumroad</a>"
        )
        buy_lbl.setOpenExternalLinks(True)
        buy_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        buy_lbl.setStyleSheet("font-size: 8.5pt;")

        card_layout.addWidget(title)
        card_layout.addWidget(info)
        card_layout.addWidget(self.license_input)
        card_layout.addWidget(self.activate_btn)
        card_layout.addWidget(self.license_status)
        card_layout.addWidget(buy_lbl)

        layout.addWidget(card)
        layout.addStretch(1)

    def _on_activate_clicked(self) -> None:
        key = self.license_input.text().strip()
        if not key:
            self.license_status.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #ef4444;")
            self.license_status.setText("License key cannot be empty.")
            return
            
        self.activate_btn.setEnabled(False)
        self.activate_btn.setText("Verifying...")
        self.license_status.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #a3a3a3;")
        self.license_status.setText("Contacting verification server...")
        
        QtCore.QTimer.singleShot(100, lambda: self._process_activation(key))
        
    def _process_activation(self, key: str) -> None:
        res = verify_gumroad_license(self.config.product_id, key)
        self.activate_btn.setEnabled(True)
        self.activate_btn.setText("Activate License")
        
        if res.get("success"):
            self.config.license_key = key
            self.config.cached_hwid = get_hardware_id()
            self.config.save()
            
            self.license_status.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #10b981;")
            self.license_status.setText("Activation successful!")
            
            QtCore.QTimer.singleShot(800, self._show_terminal_page)
        else:
            self.license_status.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #ef4444;")
            self.license_status.setText(res.get("message", "Validation failed."))

    def show_about_dialog(self) -> None:
        dialog = AboutDialog(self)
        dialog.exec()

    def _header(self) -> QtWidgets.QVBoxLayout:
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(8, 0, 8, 4)
        
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.setSpacing(8)
        
        self.maya_dot = AnimatedDot()
        self.maya_lbl = QtWidgets.QLabel("Maya")
        self.maya_lbl.setStyleSheet("color: #666666; font-size: 8.5pt; font-weight: 600;")
        
        self.blender_dot = AnimatedDot()
        self.blender_lbl = QtWidgets.QLabel("Blender")
        self.blender_lbl.setStyleSheet("color: #666666; font-size: 8.5pt; font-weight: 600;")
        
        status_layout.addWidget(self.maya_dot, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.maya_lbl, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.blender_dot, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.blender_lbl, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        status_layout.addStretch(1)
        
        self.policy_val = QtWidgets.QLabel("Direct Import")
        self.policy_val.setStyleSheet("color: #888888; font-size: 8.5pt; font-weight: 600;")
        status_layout.addWidget(self.policy_val, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addLayout(status_layout)
        return header_layout

    def _show_terminal_page(self) -> None:
        if not check_license(self.config.license_key, self.config.cached_hwid):
            self._show_license_page()
            return
        self.nav_terminal_btn.set_active(True)
        self.nav_settings_btn.set_active(False)
        self.nav_terminal_btn.setVisible(True)
        self.nav_settings_btn.setVisible(True)
        self._fade_switch_page(1)
        
    def _show_settings_page(self) -> None:
        if not check_license(self.config.license_key, self.config.cached_hwid):
            self._show_license_page()
            return
        self.nav_terminal_btn.set_active(False)
        self.nav_settings_btn.set_active(True)
        self.nav_terminal_btn.setVisible(True)
        self.nav_settings_btn.setVisible(True)
        self._fade_switch_page(2)

    def _show_license_page(self) -> None:
        self.nav_terminal_btn.setVisible(False)
        self.nav_settings_btn.setVisible(False)
        self._fade_switch_page(0)
        
    def _refresh_nav_styles(self) -> None:
        pass

    def _build_terminal_page(self) -> None:
        self.terminal_page = QtWidgets.QWidget()
        self.terminal_page.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        layout = QtWidgets.QVBoxLayout(self.terminal_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Region 1: DCC Launchpad Card
        layout.addWidget(self._build_launchpad())

        # Region 2: Bridge Control Hub Card
        layout.addWidget(self._build_bridge_hub())

        # Expandable Logger Drawer
        layout.addWidget(self._activity_drawer(), 0)

        layout.addStretch(1)

    def _build_launchpad(self) -> QtWidgets.QWidget:
        session = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(session)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        maya_btn = self._button("Launch\u00a0", self.launch_maya, primary=False, animated=False)
        maya_btn.setMinimumHeight(38)
        maya_btn.setToolTip("Launch Autodesk Maya with the connection server initialized")
        maya_icon_path = PROJECT_ROOT / "icons" / "maya_white.png"
        if maya_icon_path.exists():
            maya_btn.setIcon(QtGui.QIcon(str(maya_icon_path)))
            maya_btn.setIconSize(QtCore.QSize(13, 13))
            maya_btn.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        
        blender_btn = self._button("Launch\u00a0", self.launch_blender, primary=False, animated=False)
        blender_btn.setMinimumHeight(38)
        blender_btn.setToolTip("Launch Blender with the connection server initialized")
        blender_icon_path = PROJECT_ROOT / "icons" / "blender_white.png"
        if blender_icon_path.exists():
            blender_btn.setIcon(QtGui.QIcon(str(blender_icon_path)))
            blender_btn.setIconSize(QtCore.QSize(16, 16))
            blender_btn.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        
        layout.addWidget(maya_btn, 1)
        layout.addWidget(blender_btn, 1)
        return session

    def _build_bridge_hub(self) -> QtWidgets.QFrame:
        bridge = QtWidgets.QFrame()
        bridge.setObjectName("ControlHubFrame")
        layout = QtWidgets.QVBoxLayout(bridge)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Segment switcher container
        segment_container = QtWidgets.QWidget()
        segment_container.setObjectName("SegmentContainer")
        segment_layout = QtWidgets.QHBoxLayout(segment_container)
        segment_layout.setContentsMargins(2, 2, 2, 2)
        segment_layout.setSpacing(2)
        
        self.dir_maya_btn = AnimatedSegmentButton("Maya ➔ Blender", active=True)
        self.dir_maya_btn.setToolTip("Set transfer direction from Maya to Blender")
        self.dir_maya_btn.clicked.connect(self._on_dir_maya_clicked)
        
        self.dir_blender_btn = AnimatedSegmentButton("Blender ➔ Maya", active=False)
        self.dir_blender_btn.setToolTip("Set transfer direction from Blender to Maya")
        self.dir_blender_btn.clicked.connect(self._on_dir_blender_clicked)
        
        segment_layout.addWidget(self.dir_maya_btn, 1)
        segment_layout.addWidget(self.dir_blender_btn, 1)
        layout.addWidget(segment_container)
        
        self.flow_description_lbl = QtWidgets.QLabel("Maya Export ➔ Blender Import")
        self.flow_description_lbl.setObjectName("FlowDescription")
        self.flow_description_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.flow_description_lbl)
  
        # Centerpiece Automated Sync Button
        self.sync_btn = self._button("ROUNDTRIP SYNC", self.sync_current, primary=True)
        self.sync_btn.setMinimumHeight(44)
        self.sync_btn.setToolTip("Trigger export from source DCC and import in destination DCC automatically")
        
        layout.addWidget(self.sync_btn)
        
        # Collapsible Advanced Overrides & Policies Drawer
        self.advanced_container = QtWidgets.QWidget()
        adv_layout = QtWidgets.QVBoxLayout(self.advanced_container)
        adv_layout.setContentsMargins(0, 6, 0, 0)
        adv_layout.setSpacing(10)
        
        # Manual Overrides Actions Row Container
        override_container = QtWidgets.QWidget()
        override_container.setObjectName("TransContainer")
        override_layout = QtWidgets.QHBoxLayout(override_container)
        override_layout.setContentsMargins(0, 0, 0, 0)
        override_layout.setSpacing(8)
        
        self.export_btn = self._button("Manual Export", self.export_current)
        self.export_btn.setMinimumHeight(34)
        self.export_btn.setToolTip("Manually export selection to exchange folder without triggering import")
        
        self.import_btn = self._button("Manual Import", self.import_current)
        self.import_btn.setMinimumHeight(34)
        self.import_btn.setToolTip("Manually import the latest transfer asset into this DCC session")
        
        override_layout.addWidget(self.export_btn, 1)
        override_layout.addWidget(self.import_btn, 1)
        
        adv_form = QtWidgets.QFormLayout()
        adv_form.setContentsMargins(0, 0, 0, 0)
        adv_form.setHorizontalSpacing(14)
        adv_form.setVerticalSpacing(12)
        adv_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        adv_form.addRow("Overrides", override_container)
   
        # Policies Row Container
        self.update_existing = WordWrapCheckBox("Update existing mesh by name (preserves shaders)")
        self.update_existing.setChecked(True)
        self.update_existing.stateChanged.connect(self._on_policy_changed)
        
        self.sync_transforms = WordWrapCheckBox("Sync destination transforms and pivots")
        self.sync_transforms.setChecked(False)
        self.sync_transforms.stateChanged.connect(self._on_policy_changed)
        
        policies_container = QtWidgets.QWidget()
        policies_container.setObjectName("TransContainer")
        policies = QtWidgets.QVBoxLayout(policies_container)
        policies.setContentsMargins(0, 0, 0, 0)
        policies.setSpacing(8)
        policies.addWidget(self.update_existing)
        policies.addWidget(self.sync_transforms)
        adv_form.addRow("Policies", policies_container)
   

        
        adv_layout.addLayout(adv_form)
        self.advanced_container.setVisible(False)
        
        # Clickable Link to expand/collapse
        self.toggle_advanced_btn = QtWidgets.QPushButton("Advanced Options ▾")
        self.toggle_advanced_btn.setObjectName("CollapseToggleBtn")
        self.toggle_advanced_btn.setMinimumHeight(24)
        self.toggle_advanced_btn.setToolTip("Show or hide settings overrides and exchange folder shortcuts")
        self.toggle_advanced_btn.clicked.connect(self._toggle_advanced_controls)
        
        layout.addWidget(self.toggle_advanced_btn, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.advanced_container)
        return bridge
 
    def _toggle_advanced_controls(self) -> None:
        is_visible = self.advanced_container.isVisible() and self.advanced_container.maximumHeight() > 0
        show = not is_visible
        if show:
            self.toggle_advanced_btn.setText("Advanced Options ▴")
        else:
            self.toggle_advanced_btn.setText("Advanced Options ▾")
        self._animate_toggle_widget(self.advanced_container, show)

    def _activity_drawer(self) -> QtWidgets.QWidget:
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Console logs...")
        self.log.setMaximumHeight(110)
        self.log.setVisible(False)

        drawer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(drawer)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        
        head = QtWidgets.QHBoxLayout()
        self.toggle_console_btn = QtWidgets.QPushButton("Activity Console ▾")
        self.toggle_console_btn.setObjectName("CollapseToggleBtn")
        self.toggle_console_btn.setMinimumHeight(20)
        self.toggle_console_btn.setToolTip("Show or hide console execution logs")
        self.toggle_console_btn.clicked.connect(self._toggle_console_drawer)
        head.addWidget(self.toggle_console_btn)
        head.addStretch(1)
        
        clear_btn = self._button("Clear Logs", self.log.clear, animated=False)
        clear_btn.setObjectName("CollapseToggleBtn")
        clear_btn.setMinimumHeight(20)
        clear_btn.setFixedWidth(95)
        clear_btn.setToolTip("Clear all console execution logs")
        head.addWidget(clear_btn)
        layout.addLayout(head)
        layout.addWidget(self.log)
        return drawer

    def _toggle_console_drawer(self) -> None:
        is_visible = self.log.isVisible() and self.log.maximumHeight() > 0
        show = not is_visible
        if show:
            self.toggle_console_btn.setText("Activity Console ▴")
        else:
            self.toggle_console_btn.setText("Activity Console ▾")
        self._animate_toggle_widget(self.log, show, default_target_height=110)

    def _build_config_page(self) -> None:
        self.config_page = QtWidgets.QWidget()
        self.config_page.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Ignored)
        layout = QtWidgets.QVBoxLayout(self.config_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        paths = self._card("FileSystem Executables")
        paths_layout = paths.layout()
        self.maya_path = self._path_row(paths_layout, "Maya Executable", self._browse_maya)
        self.blender_path = self._path_row(paths_layout, "Blender Executable", self._browse_blender)
        self.exchange_path = QtWidgets.QLineEdit()
        browse_exchange_btn = AnimatedButton("Browse")
        browse_exchange_btn.setFixedWidth(70)
        browse_exchange_btn.setToolTip("Browse and select exchange directory path")
        browse_exchange_btn.clicked.connect(self._browse_exchange)
        
        open_exchange_btn = self._button("Open Exchange Folder", self.open_exchange)
        open_exchange_btn.setIcon(self.create_vector_icon("folder", "#ffffff"))
        open_exchange_btn.setIconSize(QtCore.QSize(14, 14))
        open_exchange_btn.setToolTip("Open the active FBX asset exchange folder in File Explorer")
        
        exchange_container = QtWidgets.QWidget()
        exchange_layout = QtWidgets.QVBoxLayout(exchange_container)
        exchange_layout.setContentsMargins(0, 0, 0, 0)
        exchange_layout.setSpacing(6)
        
        path_row = QtWidgets.QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(6)
        path_row.addWidget(self.exchange_path, 1)
        path_row.addWidget(browse_exchange_btn)
        
        exchange_layout.addLayout(path_row)
        exchange_layout.addWidget(open_exchange_btn)
        paths_layout.addRow("Exchange Directory", exchange_container)
        layout.addWidget(paths)

        ports = self._card("Connection Ports")
        ports_layout = ports.layout()
        self.maya_port = QtWidgets.QSpinBox()
        self.maya_port.setRange(1024, 65535)
        self.blender_port = QtWidgets.QSpinBox()
        self.blender_port.setRange(1024, 65535)
        ports_layout.addRow("Maya Server Port", self.maya_port)
        ports_layout.addRow("Blender Server Port", self.blender_port)
        layout.addWidget(ports)

        scripts_box = self._card("Startup Scripts")
        scripts_layout = scripts_box.layout()
        
        copy_m = self._button("Copy For Maya", self.copy_maya_bootstrap)
        copy_m.setToolTip("Copy the Maya connection startup script to the clipboard")
        
        copy_b = self._button("Copy For Blender", self.copy_blender_bootstrap)
        copy_b.setToolTip("Copy the Blender connection startup script to the clipboard")
        
        scripts_row = QtWidgets.QHBoxLayout()
        scripts_row.setSpacing(8)
        scripts_row.addWidget(copy_m, 1)
        scripts_row.addWidget(copy_b, 1)
        scripts_layout.addRow("", scripts_row)
        layout.addWidget(scripts_box)

        save_btn = self._button("Save Settings", lambda: self.save_config(verbose=True), primary=True)
        save_btn.setMinimumHeight(38)
        save_btn.setToolTip("Save configuration paths and ports to disk")
        layout.addWidget(save_btn)

        layout.addStretch(1)

    def _card(self, title: str) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(title)
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        return box

    def _button(self, label: str, callback, primary: bool = False, animated: bool = True) -> QtWidgets.QPushButton:
        if animated:
            button = AnimatedButton(label, primary=primary)
        else:
            button = QtWidgets.QPushButton(label)
            button.setObjectName("PrimaryBtn" if primary else "GhostBtn")
        button.clicked.connect(callback)
        button.setMinimumHeight(30)
        return button

    def _path_row(self, layout: QtWidgets.QFormLayout, label: str, browse_callback) -> QtWidgets.QLineEdit:
        edit = QtWidgets.QLineEdit()
        browse = AnimatedButton("Browse")
        browse.setFixedWidth(70)
        browse.setToolTip(f"Browse and select {label.lower()} path")
        browse.clicked.connect(browse_callback)
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(edit, 1)
        row.addWidget(browse)
        layout.addRow(label, row)
        return edit

    def _load_config_to_ui(self) -> None:
        self.maya_path.setText(self.config.maya_exe)
        self.blender_path.setText(self.config.blender_exe)
        self.exchange_path.setText(self.config.exchange_dir)
        self.maya_port.setValue(self.config.maya_port)
        self.blender_port.setValue(self.config.blender_port)
        self._on_policy_changed()
        self._update_direction_ui()

    def _on_dir_maya_clicked(self) -> None:
        self.direction = "maya"
        self._update_direction_ui()
        self._message("Transmission flow set to: Maya ➔ Blender.")

    def _on_dir_blender_clicked(self) -> None:
        self.direction = "blender"
        self._update_direction_ui()
        self._message("Transmission flow set to: Blender ➔ Maya.")

    def _update_direction_ui(self) -> None:
        if self.direction == "maya":
            self.dir_maya_btn.set_active(True)
            self.dir_blender_btn.set_active(False)
            self.flow_description_lbl.setText("Maya Export ➔ Blender Import")
        else:
            self.dir_maya_btn.set_active(False)
            self.dir_blender_btn.set_active(True)
            self.flow_description_lbl.setText("Blender Export ➔ Maya Import")

    def _on_policy_changed(self) -> None:
        if self.update_existing.isChecked():
            if self.sync_transforms.isChecked():
                self.policy_val.setText("Update + Transform Sync")
            else:
                self.policy_val.setText("Update by Name")
        else:
            if self.sync_transforms.isChecked():
                self.policy_val.setText("Transform Sync Only")
            else:
                self.policy_val.setText("Direct Import")

    def export_current(self) -> None:
        self.run_dcc_action(self.direction, "export")

    def import_current(self) -> None:
        target_host = "blender" if self.direction == "maya" else "maya"
        self.run_dcc_action(target_host, "import")

    def sync_current(self) -> None:
        self.export_current()
        self.import_current()

    def save_config(self, verbose: bool = True) -> None:
        self.config.maya_exe = self.maya_path.text().strip()
        self.config.blender_exe = self.blender_path.text().strip()
        self.config.exchange_dir = self.exchange_path.text().strip()
        self.config.maya_port = int(self.maya_port.value())
        self.config.blender_port = int(self.blender_port.value())
        self.config.save()
        Path(self.config.exchange_dir).mkdir(parents=True, exist_ok=True)
        if verbose:
            self._message("System configurations saved successfully.")

    def launch_maya(self) -> None:
        self.save_config(verbose=False)
        exe = Path(self.config.maya_exe)
        command = maya_bootstrap_command(PROJECT_ROOT, self.config.maya_port)
        self._launch([str(exe), "-command", command], "Maya")

    def launch_blender(self) -> None:
        self.save_config(verbose=False)
        exe = Path(self.config.blender_exe)
        expr = blender_bootstrap_expr(PROJECT_ROOT, self.config.blender_port)
        self._launch([str(exe), "--python-expr", expr], "Blender")

    def run_dcc_action(self, host: str, action: str) -> None:
        self.save_config(verbose=False)
        port = self.config.maya_port if host == "maya" else self.config.blender_port
        code = bridge_action_code(
            host,
            action,
            Path(self.config.exchange_dir),
            update_existing=self.update_existing.isChecked(),
            sync_transforms=self.sync_transforms.isChecked(),
            freeze_transforms=True,
        )
        try:
            response = send_python(port, code)
            self._mark_connected(host)
            self._message(f"{host.title()} {action}: {response}".strip())
        except Exception as exc:
            self._message(f"{host.title()} is not connected: {exc}")
            self._copy_text(code)
            self._message(f"Copied fallback {host} {action} script to clipboard.")

    def copy_maya_bootstrap(self) -> None:
        self._copy_text(maya_bootstrap_command(PROJECT_ROOT, self.config.maya_port))
        self._message("Maya server bootstrap command copied to clipboard.")

    def copy_blender_bootstrap(self) -> None:
        self._copy_text(blender_bootstrap_expr(PROJECT_ROOT, self.config.blender_port))
        self._message("Blender server bootstrap expression copied to clipboard.")

    def open_exchange(self) -> None:
        self.save_config(verbose=False)
        path = Path(self.config.exchange_dir)
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def _browse_maya(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Maya executable", self.maya_path.text(), "Executable (*.exe)"
        )
        if path:
            self.maya_path.setText(path)

    def _browse_blender(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Blender executable", self.blender_path.text(), "Executable (*.exe)"
        )
        if path:
            self.blender_path.setText(path)

    def _browse_exchange(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select exchange folder", self.exchange_path.text())
        if path:
            self.exchange_path.setText(path)

    def _launch(self, command: list[str], label: str) -> None:
        exe = Path(command[0])
        if not exe.exists():
            self._message(f"{label} executable not found: {exe}")
            return
            
        env = os.environ.copy()
        for key in ["PYTHONPATH", "PYTHONHOME"]:
            env.pop(key, None)
        if "PYTHONPATH_pre_pyinstaller" in env:
            env["PYTHONPATH"] = env.pop("PYTHONPATH_pre_pyinstaller")
            
        dcc_src = PROJECT_ROOT / "dcc_sources"
        env["FLUX_BRIDGE_ROOT"] = str(dcc_src if dcc_src.exists() else PROJECT_ROOT)
        
        import sys
        if getattr(sys, 'frozen', False):
            working_dir = Path(sys.executable).parent.resolve()
        else:
            working_dir = PROJECT_ROOT
            
        subprocess.Popen(command, cwd=str(working_dir), env=env)
        self._message(f"Launching {label} server instance...")

    def _mark_connected(self, host: str) -> None:
        if host == "maya":
            self._set_dot_state(self.maya_dot, True)
        else:
            self._set_dot_state(self.blender_dot, True)

    def _copy_text(self, text: str) -> None:
        QtWidgets.QApplication.clipboard().setText(text)

    def _message(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {text}")


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setApplicationName("Flux - Maya Blender Asset Bridge (FBX)")
    
    from bridge_core.settings import PROJECT_ROOT
    flux_icon_path = PROJECT_ROOT / "icons" / "flux_logo.png"
    if flux_icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(flux_icon_path)))
        
    window = FluxWindow()
    window.show()
    return app.exec()
