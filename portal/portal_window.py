from __future__ import annotations

import os
import math
import subprocess
from datetime import datetime
from pathlib import Path

# pyrefly: ignore [missing-import]
from PyQt6 import QtCore, QtGui, QtWidgets

from bridge_core.settings import PROJECT_ROOT
from .config import PortalConfig
from .dcc_commands import blender_bootstrap_expr, bridge_action_code, maya_bootstrap_command
from .styles import DARK_NEON_QSS
from .transport import send_python


class PortalWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = PortalConfig.load()
        self.direction = "maya"
        self.setWindowTitle("Portal - Maya Blender Asset Bridge (FBX)")
        self.resize(380, 700)
        self.setMinimumSize(360, 640)
        
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
        portal_icon_path = PROJECT_ROOT / "icons" / "portal_logo.png"
        if portal_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(portal_icon_path)))
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
            
        painter.end()
        return QtGui.QIcon(pixmap)

    def _set_dot_state(self, dot: QtWidgets.QLabel, is_active: bool) -> None:
        if is_active:
            dot.setStyleSheet("background-color: #10b981; border-radius: 3px;")
        else:
            dot.setStyleSheet("background-color: #333333; border-radius: 3px;")

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 18)
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
        self.close_dot.clicked.connect(self.close)
        
        close_glow = QtWidgets.QGraphicsDropShadowEffect(self.close_dot)
        close_glow.setBlurRadius(8)
        close_glow.setXOffset(0)
        close_glow.setYOffset(0)
        close_glow.setColor(QtGui.QColor("#ff5f56"))
        self.close_dot.setGraphicsEffect(close_glow)
        
        self.min_dot = QtWidgets.QPushButton()
        self.min_dot.setFixedSize(12, 12)
        self.min_dot.setObjectName("MinDot")
        self.min_dot.clicked.connect(self.showMinimized)
        
        min_glow = QtWidgets.QGraphicsDropShadowEffect(self.min_dot)
        min_glow.setBlurRadius(8)
        min_glow.setXOffset(0)
        min_glow.setYOffset(0)
        min_glow.setColor(QtGui.QColor("#ffbd2e"))
        self.min_dot.setGraphicsEffect(min_glow)
        
        title_lbl = QtWidgets.QLabel("P O R T A L")
        title_lbl.setObjectName("TitleBarTitle")
        title_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        title_glow = QtWidgets.QGraphicsDropShadowEffect(title_lbl)
        title_glow.setBlurRadius(15)
        title_glow.setXOffset(0)
        title_glow.setYOffset(0)
        title_glow.setColor(QtGui.QColor(255, 255, 255, 120))
        title_lbl.setGraphicsEffect(title_glow)
        
        title_bar_layout.addWidget(self.close_dot)
        title_bar_layout.addWidget(self.min_dot)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(title_lbl)
        title_bar_layout.addStretch(1)
        
        right_spacer = QtWidgets.QWidget()
        right_spacer.setFixedSize(32, 12)
        title_bar_layout.addWidget(right_spacer)
        
        root.addWidget(title_bar)

        # 1. Header Navigation
        root.addLayout(self._header())

        # Vercel navigation switcher
        nav_container = QtWidgets.QWidget()
        nav_container.setObjectName("NavContainer")
        nav_layout = QtWidgets.QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(2, 2, 2, 2)
        nav_layout.setSpacing(2)
        
        self.nav_terminal_btn = QtWidgets.QPushButton("Terminal")
        self.nav_terminal_btn.setObjectName("NavBtnActive")
        self.nav_terminal_btn.clicked.connect(self._show_terminal_page)
        
        self.nav_settings_btn = QtWidgets.QPushButton("Settings")
        self.nav_settings_btn.setObjectName("NavBtnInactive")
        self.nav_settings_btn.clicked.connect(self._show_settings_page)
        
        nav_layout.addWidget(self.nav_terminal_btn, 1)
        nav_layout.addWidget(self.nav_settings_btn, 1)
        
        root.addWidget(nav_container)

        # 2. Main Stacked page views
        self.central_stack = QtWidgets.QStackedWidget()
        
        self._build_terminal_page()
        self._build_config_page()
        
        self.central_stack.addWidget(self.terminal_page)
        self.central_stack.addWidget(self.config_page)
        
        root.addWidget(self.central_stack, 1)

        self._show_terminal_page()

    def _header(self) -> QtWidgets.QVBoxLayout:
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(8, 0, 8, 4)
        
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.setSpacing(8)
        
        self.maya_dot = QtWidgets.QLabel()
        self.maya_dot.setFixedSize(6, 6)
        self.maya_lbl = QtWidgets.QLabel("Maya")
        self.maya_lbl.setStyleSheet("color: #666666; font-size: 8.5pt; font-weight: 600;")
        
        self.blender_dot = QtWidgets.QLabel()
        self.blender_dot.setFixedSize(6, 6)
        self.blender_lbl = QtWidgets.QLabel("Blender")
        self.blender_lbl.setStyleSheet("color: #666666; font-size: 8.5pt; font-weight: 600;")
        
        status_layout.addWidget(self.maya_dot)
        status_layout.addWidget(self.maya_lbl)
        status_layout.addWidget(self.blender_dot)
        status_layout.addWidget(self.blender_lbl)
        status_layout.addStretch(1)
        
        self.policy_val = QtWidgets.QLabel("Direct Import")
        self.policy_val.setStyleSheet("color: #888888; font-size: 8.5pt; font-weight: 600;")
        status_layout.addWidget(self.policy_val)
        
        header_layout.addLayout(status_layout)
        return header_layout

    def _show_terminal_page(self) -> None:
        self.central_stack.setCurrentIndex(0)
        self.nav_terminal_btn.setObjectName("NavBtnActive")
        self.nav_settings_btn.setObjectName("NavBtnInactive")
        self._refresh_nav_styles()
        
    def _show_settings_page(self) -> None:
        self.central_stack.setCurrentIndex(1)
        self.nav_terminal_btn.setObjectName("NavBtnInactive")
        self.nav_settings_btn.setObjectName("NavBtnActive")
        self._refresh_nav_styles()
        
    def _refresh_nav_styles(self) -> None:
        self.nav_terminal_btn.style().unpolish(self.nav_terminal_btn)
        self.nav_terminal_btn.style().polish(self.nav_terminal_btn)
        self.nav_settings_btn.style().unpolish(self.nav_settings_btn)
        self.nav_settings_btn.style().polish(self.nav_settings_btn)

    def _build_terminal_page(self) -> None:
        self.terminal_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.terminal_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Region 1: DCC Launchpad Card
        layout.addWidget(self._build_launchpad())

        # Region 2: Bridge Control Hub Card
        layout.addWidget(self._build_bridge_hub())

        layout.addStretch(1)

        # Expandable Logger Drawer
        layout.addWidget(self._activity_drawer(), 0)

    def _build_launchpad(self) -> QtWidgets.QWidget:
        session = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(session)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        maya_btn = self._button("Launch ", self.launch_maya, primary=False)
        maya_btn.setMinimumHeight(38)
        maya_icon_path = PROJECT_ROOT / "icons" / "maya_white.png"
        if maya_icon_path.exists():
            maya_btn.setIcon(QtGui.QIcon(str(maya_icon_path)))
            maya_btn.setIconSize(QtCore.QSize(13, 13))
            maya_btn.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        
        blender_btn = self._button("Launch ", self.launch_blender, primary=False)
        blender_btn.setMinimumHeight(38)
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
        
        self.dir_maya_btn = QtWidgets.QPushButton("Maya ➔ Blender")
        self.dir_maya_btn.setObjectName("SegmentActive")
        self.dir_maya_btn.clicked.connect(self._on_dir_maya_clicked)
        
        self.dir_blender_btn = QtWidgets.QPushButton("Blender ➔ Maya")
        self.dir_blender_btn.setObjectName("SegmentInactive")
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
        
        sync_glow = QtWidgets.QGraphicsDropShadowEffect(self.sync_btn)
        sync_glow.setBlurRadius(15)
        sync_glow.setXOffset(0)
        sync_glow.setYOffset(0)
        sync_glow.setColor(QtGui.QColor(255, 255, 255, 100))
        self.sync_btn.setGraphicsEffect(sync_glow)
        
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
        
        self.import_btn = self._button("Manual Import", self.import_current)
        self.import_btn.setMinimumHeight(34)
        
        override_layout.addWidget(self.export_btn, 1)
        override_layout.addWidget(self.import_btn, 1)
        
        adv_form = QtWidgets.QFormLayout()
        adv_form.setContentsMargins(0, 0, 0, 0)
        adv_form.setHorizontalSpacing(14)
        adv_form.setVerticalSpacing(12)
        adv_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        adv_form.addRow("Overrides", override_container)
  
        # Policies Row Container
        self.update_existing = QtWidgets.QCheckBox("Update existing mesh by name (preserves shaders)")
        self.update_existing.setChecked(True)
        self.update_existing.stateChanged.connect(self._on_policy_changed)
        
        self.sync_transforms = QtWidgets.QCheckBox("Sync destination transforms and pivots")
        self.sync_transforms.setChecked(False)
        self.sync_transforms.stateChanged.connect(self._on_policy_changed)
        
        policies_container = QtWidgets.QWidget()
        policies_container.setObjectName("TransContainer")
        policies = QtWidgets.QVBoxLayout(policies_container)
        policies.setContentsMargins(0, 0, 0, 0)
        policies.setSpacing(6)
        policies.addWidget(self.update_existing)
        policies.addWidget(self.sync_transforms)
        adv_form.addRow("Policies", policies_container)
  
        # Exchange folder shortcut path row container
        exchange_container = QtWidgets.QWidget()
        exchange_container.setObjectName("TransContainer")
        exchange_row = QtWidgets.QHBoxLayout(exchange_container)
        exchange_row.setContentsMargins(0, 0, 0, 0)
        exchange_row.setSpacing(6)
        
        self.exchange_label = QtWidgets.QLabel("")
        self.exchange_label.setObjectName("PathLabel")
        self.exchange_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        
        open_folder_btn = self._button("Open Folder", self.open_exchange)
        open_folder_btn.setIcon(self.create_vector_icon("folder", "#ffffff"))
        open_folder_btn.setIconSize(QtCore.QSize(14, 14))
        open_folder_btn.setFixedWidth(110)
        
        exchange_row.addWidget(self.exchange_label, 1)
        exchange_row.addWidget(open_folder_btn)
        adv_form.addRow("Exchange Path", exchange_container)
        
        adv_layout.addLayout(adv_form)
        self.advanced_container.setVisible(False)
        
        # Clickable Link to expand/collapse
        self.toggle_advanced_btn = QtWidgets.QPushButton("Advanced Options ▾")
        self.toggle_advanced_btn.setObjectName("CollapseToggleBtn")
        self.toggle_advanced_btn.setMinimumHeight(24)
        self.toggle_advanced_btn.clicked.connect(self._toggle_advanced_controls)
        
        layout.addWidget(self.toggle_advanced_btn, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.advanced_container)
        return bridge
 
    def _toggle_advanced_controls(self) -> None:
        is_visible = self.advanced_container.isVisible()
        self.advanced_container.setVisible(not is_visible)
        if is_visible:
            self.toggle_advanced_btn.setText("Advanced Options ▾")
        else:
            self.toggle_advanced_btn.setText("Advanced Options ▴")

    def _activity_drawer(self) -> QtWidgets.QWidget:
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Console logs...")
        self.log.setMaximumHeight(110)

        drawer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(drawer)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        
        head = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Activity Console")
        lbl.setStyleSheet("font-weight: bold; color: #666666; font-size: 8.5pt;")
        head.addWidget(lbl)
        head.addStretch(1)
        
        clear_btn = self._button("Clear Logs", self.log.clear)
        clear_btn.setObjectName("CollapseToggleBtn")
        clear_btn.setMinimumHeight(20)
        clear_btn.setFixedWidth(80)
        head.addWidget(clear_btn)
        layout.addLayout(head)
        layout.addWidget(self.log)
        return drawer

    def _build_config_page(self) -> None:
        self.config_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.config_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        paths = self._card("FileSystem Executables")
        paths_layout = paths.layout()
        self.maya_path = self._path_row(paths_layout, "Maya Executable", self._browse_maya)
        self.blender_path = self._path_row(paths_layout, "Blender Executable", self._browse_blender)
        self.exchange_path = self._path_row(paths_layout, "Exchange Directory", self._browse_exchange)
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
        
        copy_m = self._button("For Maya", self.copy_maya_bootstrap)
        copy_b = self._button("For Blender", self.copy_blender_bootstrap)
        
        scripts_row = QtWidgets.QHBoxLayout()
        scripts_row.setSpacing(8)
        scripts_row.addWidget(copy_m, 1)
        scripts_row.addWidget(copy_b, 1)
        scripts_layout.addRow("", scripts_row)
        layout.addWidget(scripts_box)

        save_btn = self._button("Save Settings", self.save_config, primary=True)
        save_btn.setMinimumHeight(38)
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

    def _button(self, label: str, callback, primary: bool = False) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(label)
        button.setObjectName("PrimaryBtn" if primary else "GhostBtn")
        button.clicked.connect(callback)
        button.setMinimumHeight(30)
        return button

    def _path_row(self, layout: QtWidgets.QFormLayout, label: str, browse_callback) -> QtWidgets.QLineEdit:
        edit = QtWidgets.QLineEdit()
        browse = QtWidgets.QPushButton("Browse")
        browse.setObjectName("GhostBtn")
        browse.setFixedWidth(70)
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
        self.exchange_label.setText(self.config.exchange_dir)
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
            self.dir_maya_btn.setObjectName("SegmentActive")
            self.dir_blender_btn.setObjectName("SegmentInactive")
            self.flow_description_lbl.setText("Maya Export ➔ Blender Import")
        else:
            self.dir_maya_btn.setObjectName("SegmentInactive")
            self.dir_blender_btn.setObjectName("SegmentActive")
            self.flow_description_lbl.setText("Blender Export ➔ Maya Import")
            
        for btn in (self.dir_maya_btn, self.dir_blender_btn):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

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

    def save_config(self) -> None:
        self.config.maya_exe = self.maya_path.text().strip()
        self.config.blender_exe = self.blender_path.text().strip()
        self.config.exchange_dir = self.exchange_path.text().strip()
        self.config.maya_port = int(self.maya_port.value())
        self.config.blender_port = int(self.blender_port.value())
        self.config.save()
        Path(self.config.exchange_dir).mkdir(parents=True, exist_ok=True)
        self.exchange_label.setText(self.config.exchange_dir)
        self._message("System configurations saved successfully.")

    def launch_maya(self) -> None:
        self.save_config()
        exe = Path(self.config.maya_exe)
        command = maya_bootstrap_command(PROJECT_ROOT, self.config.maya_port)
        self._launch([str(exe), "-command", command], "Maya")

    def launch_blender(self) -> None:
        self.save_config()
        exe = Path(self.config.blender_exe)
        expr = blender_bootstrap_expr(PROJECT_ROOT, self.config.blender_port)
        self._launch([str(exe), "--python-expr", expr], "Blender")

    def run_dcc_action(self, host: str, action: str) -> None:
        self.save_config()
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
        self.save_config()
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
            
        env["PORTAL_BRIDGE_ROOT"] = str(PROJECT_ROOT)
        
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
    app.setApplicationName("Portal - Maya Blender Asset Bridge (FBX)")
    
    from bridge_core.settings import PROJECT_ROOT
    portal_icon_path = PROJECT_ROOT / "icons" / "portal_logo.png"
    if portal_icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(portal_icon_path)))
        
    window = PortalWindow()
    window.show()
    return app.exec()
