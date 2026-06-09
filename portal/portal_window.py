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
        self.resize(460, 780)
        self.setMinimumSize(420, 680)
        self.setStyleSheet(DARK_NEON_QSS)
        
        # Set gorgeous branded window icon
        portal_icon_path = PROJECT_ROOT / "icons" / "portal.png"
        if portal_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(portal_icon_path)))
        else:
            window_icon = self.create_vector_icon("maya")
            if window_icon:
                self.setWindowIcon(window_icon)
            
        self._build_ui()
        self._load_config_to_ui()

    def create_vector_icon(self, name: str, color_hex: str = "#38bdf8") -> QtGui.QIcon:
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

    def apply_neon_glow(self, widget: QtWidgets.QWidget, color_hex: str = "#38bdf8", radius: int = 12) -> None:
        """Applies hardware-accelerated, high-fidelity neon drop-shadow glow to widgets."""
        effect = QtWidgets.QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(radius)
        effect.setXOffset(0)
        effect.setYOffset(0)
        effect.setColor(QtGui.QColor(color_hex))
        widget.setGraphicsEffect(effect)

    def _create_status_pill(self, label_text: str, status_text: str, is_active: bool = False) -> tuple[QtWidgets.QWidget, QtWidgets.QLabel, QtWidgets.QLabel]:
        pill = QtWidgets.QWidget()
        pill.setObjectName("StatusPill")
        layout = QtWidgets.QHBoxLayout(pill)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        
        dot = QtWidgets.QLabel()
        dot.setFixedSize(8, 8)
        self._set_dot_state(dot, is_active)
        
        lbl = QtWidgets.QLabel(label_text.upper() + ":")
        lbl.setObjectName("StatusLabel")
        
        val = QtWidgets.QLabel(status_text)
        val.setObjectName("StatusText")
        
        layout.addWidget(dot)
        layout.addWidget(lbl)
        layout.addWidget(val)
        return pill, dot, val

    def _set_dot_state(self, dot: QtWidgets.QLabel, is_active: bool) -> None:
        if is_active:
            dot.setStyleSheet("background-color: #10b981; border-radius: 4px; border: 1px solid #34d399;")
        else:
            dot.setStyleSheet("background-color: #64748b; border-radius: 4px; border: 1px solid #94a3b8;")

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(12)

        # 1. High-Tech Header Navigation
        root.addLayout(self._header())

        # Separator Frame line
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); max-height: 1px; border: none;")
        root.addWidget(sep)

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
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Brand Title and Navigation Buttons
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)
        
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(6)
        brand_icon = QtWidgets.QLabel()
        portal_icon_path = PROJECT_ROOT / "icons" / "portal.png"
        if portal_icon_path.exists():
            pixmap = QtGui.QPixmap(str(portal_icon_path))
            scaled_pixmap = pixmap.scaled(36, 36, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            brand_icon.setPixmap(scaled_pixmap)
        else:
            brand_icon.setText("✦")
            brand_icon.setStyleSheet("color: #38bdf8; font-size: 16pt; font-weight: bold;")
        title = QtWidgets.QLabel("Portal")
        title.setObjectName("HeroTitle")
        title.setStyleSheet("font-size: 16pt; font-weight: 800; color: #ffffff;")
        
        title_layout.addWidget(brand_icon)
        title_layout.addWidget(title)
        title_layout.addStretch(1)
        
        # Navigation Links
        self.nav_terminal_btn = QtWidgets.QPushButton("Terminal")
        self.nav_terminal_btn.setObjectName("NavBtnActive")
        self.nav_terminal_btn.setMinimumHeight(28)
        self.nav_terminal_btn.setIcon(self.create_vector_icon("sync", "#38bdf8"))
        self.nav_terminal_btn.setIconSize(QtCore.QSize(14, 14))
        self.nav_terminal_btn.clicked.connect(self._show_terminal_page)
        
        self.nav_settings_btn = QtWidgets.QPushButton("Settings")
        self.nav_settings_btn.setObjectName("NavBtnInactive")
        self.nav_settings_btn.setMinimumHeight(28)
        self.nav_settings_btn.setIcon(self.create_vector_icon("settings", "#64748b"))
        self.nav_settings_btn.setIconSize(QtCore.QSize(14, 14))
        self.nav_settings_btn.clicked.connect(self._show_settings_page)
        
        top_row.addLayout(title_layout, 1)
        top_row.addWidget(self.nav_terminal_btn)
        top_row.addWidget(self.nav_settings_btn)
        
        # Row 2: Status pills row (highly compact and aligned)
        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(6)
        
        # Create connection indicators
        self.maya_pill, self.maya_dot, self.maya_val = self._create_status_pill("Maya", "Idle", False)
        self.blender_pill, self.blender_dot, self.blender_val = self._create_status_pill("Blender", "Idle", False)
        self.mode_pill, self.policy_dot, self.policy_val = self._create_status_pill("Policy", "Update", True)
        
        status_row.addWidget(self.maya_pill)
        status_row.addWidget(self.blender_pill)
        status_row.addWidget(self.mode_pill)
        status_row.addStretch(1)
        
        header_layout.addLayout(top_row)
        header_layout.addLayout(status_row)
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
        """Constructs Region 1 and Region 2 in a simplified vertical layouts stack."""
        self.terminal_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.terminal_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Region 1: DCC Launchpad Card
        layout.addWidget(self._build_launchpad())

        # Region 2: Bridge Control Hub Card
        layout.addWidget(self._build_bridge_hub())

        # Push layout to the top to prevent awkward stretching of elements!
        layout.addStretch(1)

        # Expandable Logger Drawer
        layout.addWidget(self._activity_drawer(), 0)

    def _build_launchpad(self) -> QtWidgets.QWidget:
        """Region 1: Launchpad"""
        session = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(session)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        maya_btn = self._button("Launch Maya", self.launch_maya, primary=True)
        maya_btn.setIcon(self.create_vector_icon("maya", "#ffffff"))
        maya_btn.setIconSize(QtCore.QSize(18, 18))
        maya_btn.setMinimumHeight(44)
        self.apply_neon_glow(maya_btn, "#1d4ed8", 10)
        
        blender_btn = self._button("Launch Blender", self.launch_blender, primary=True)
        blender_btn.setIcon(self.create_vector_icon("blender", "#ffffff"))
        blender_btn.setIconSize(QtCore.QSize(18, 18))
        blender_btn.setMinimumHeight(44)
        self.apply_neon_glow(blender_btn, "#d97706", 10)
        
        layout.addWidget(maya_btn, 1)
        layout.addWidget(blender_btn, 1)
        return session
 
    def _build_bridge_hub(self) -> QtWidgets.QFrame:
        """Region 2: Bridge Control Hub"""
        bridge = QtWidgets.QFrame()
        bridge.setObjectName("ControlHubFrame")
        layout = QtWidgets.QVBoxLayout(bridge)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        # Section title in upper-case high-tech accent
        title_lbl = QtWidgets.QLabel("BRIDGE CONTROL HUB")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 9.5pt; color: #38bdf8; letter-spacing: 0.5px;")
        layout.addWidget(title_lbl)
        
        # Interactive Direction Selection Cards
        flow_layout = QtWidgets.QHBoxLayout()
        flow_layout.setSpacing(10)
        
        self.dir_maya_btn = QtWidgets.QPushButton()
        self.dir_maya_btn.setText("Maya ➔ Blender")
        self.dir_maya_btn.setIcon(self.create_vector_icon("maya", "#38bdf8"))
        self.dir_maya_btn.setIconSize(QtCore.QSize(18, 18))
        self.dir_maya_btn.setMinimumHeight(48)
        self.dir_maya_btn.clicked.connect(self._on_dir_maya_clicked)
        
        self.dir_blender_btn = QtWidgets.QPushButton()
        self.dir_blender_btn.setText("Blender ➔ Maya")
        self.dir_blender_btn.setIcon(self.create_vector_icon("blender", "#f97316"))
        self.dir_blender_btn.setIconSize(QtCore.QSize(18, 18))
        self.dir_blender_btn.setMinimumHeight(48)
        self.dir_blender_btn.clicked.connect(self._on_dir_blender_clicked)
        
        flow_layout.addWidget(self.dir_maya_btn, 1)
        flow_layout.addWidget(self.dir_blender_btn, 1)
        
        # We put Flow Direction in a horizontal block
        flow_widget = QtWidgets.QWidget()
        flow_vbox = QtWidgets.QVBoxLayout(flow_widget)
        flow_vbox.setContentsMargins(0, 0, 0, 0)
        flow_vbox.setSpacing(8)
        
        flow_title = QtWidgets.QLabel("ACTIVE PIPELINE FLOW DIRECTION")
        flow_title.setStyleSheet("font-weight: 700; font-size: 8pt; color: #64748b;")
        
        # Dynamic helpful description subtitle line
        self.flow_description_lbl = QtWidgets.QLabel("")
        self.flow_description_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.flow_description_lbl.setStyleSheet("font-size: 9pt; font-weight: 600; padding: 2px;")
        
        flow_vbox.addWidget(flow_title)
        flow_vbox.addLayout(flow_layout)
        flow_vbox.addWidget(self.flow_description_lbl)
        layout.addWidget(flow_widget)
 
        # Centerpiece Automated Sync Button
        self.sync_btn = self._button("ROUNDTRIP SYNC", self.sync_current)
        self.sync_btn.setIcon(self.create_vector_icon("sync", "#ffffff"))
        self.sync_btn.setIconSize(QtCore.QSize(20, 20))
        self.sync_btn.setMinimumHeight(46)
        self.sync_btn.setStyleSheet("font-size: 11pt; font-weight: 800; color: #ffffff; background-color: #2563eb; letter-spacing: 0.5px;")
        self.apply_neon_glow(self.sync_btn, "#2563eb", 12)
        
        sync_widget = QtWidgets.QWidget()
        sync_vbox = QtWidgets.QVBoxLayout(sync_widget)
        sync_vbox.setContentsMargins(0, 4, 0, 4)
        sync_vbox.setSpacing(6)
        sync_title = QtWidgets.QLabel("AUTOMATED ASSET TRANSMISSION")
        sync_title.setStyleSheet("font-weight: 700; font-size: 8pt; color: #64748b;")
        sync_vbox.addWidget(sync_title)
        sync_vbox.addWidget(self.sync_btn)
        layout.addWidget(sync_widget)
        
        # Collapsible Advanced Overrides & Policies Drawer to minimize clutter
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
        
        self.export_btn = self._button("Manual Export Current", self.export_current, primary=True)
        self.export_btn.setIcon(self.create_vector_icon("export", "#ffffff"))
        self.export_btn.setIconSize(QtCore.QSize(16, 16))
        
        self.import_btn = self._button("Manual Import Latest", self.import_current)
        self.import_btn.setIcon(self.create_vector_icon("import", "#cbd5e1"))
        self.import_btn.setIconSize(QtCore.QSize(16, 16))
        
        override_layout.addWidget(self.export_btn, 1)
        override_layout.addWidget(self.import_btn, 1)
        
        adv_form = QtWidgets.QFormLayout()
        adv_form.setContentsMargins(0, 0, 0, 0)
        adv_form.setHorizontalSpacing(14)
        adv_form.setVerticalSpacing(12)
        adv_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        adv_form.addRow("Manual Overrides", override_container)
 
        # Policies Row Container
        self.update_existing = QtWidgets.QCheckBox("Update existing mesh by name (preserves shaders)")
        self.update_existing.setChecked(True)
        self.update_existing.stateChanged.connect(self._on_policy_changed)
        
        self.sync_transforms = QtWidgets.QCheckBox("Sync destination transforms and pivots")
        self.sync_transforms.setChecked(False)
        self.sync_transforms.stateChanged.connect(self._on_policy_changed)
        
        policies_container = QtWidgets.QWidget()
        policies_container.setObjectName("TransContainer")
        policies = QtWidgets.QHBoxLayout(policies_container)
        policies.setContentsMargins(0, 0, 0, 0)
        policies.setSpacing(12)
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
        open_folder_btn.setIcon(self.create_vector_icon("folder", "#94a3b8"))
        open_folder_btn.setIconSize(QtCore.QSize(14, 14))
        open_folder_btn.setFixedWidth(110)
        
        exchange_row.addWidget(self.exchange_label, 1)
        exchange_row.addWidget(open_folder_btn)
        adv_form.addRow("Exchange Path", exchange_container)
        
        adv_layout.addLayout(adv_form)
        self.advanced_container.setVisible(False)  # Hidden by default to avoid clutter!
        
        # Clickable Link to expand/collapse
        self.toggle_advanced_btn = QtWidgets.QPushButton("Show Advanced Overrides & Policies ▾")
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
            self.toggle_advanced_btn.setText("Show Advanced Overrides & Policies ▾")
        else:
            self.toggle_advanced_btn.setText("Hide Advanced Overrides & Policies ▴")

    def _activity_drawer(self) -> QtWidgets.QWidget:
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Operations console initialized...")
        self.log.setMaximumHeight(140)

        drawer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(drawer)
        layout.setContentsMargins(2, 6, 2, 2)
        layout.setSpacing(6)
        
        head = QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel()
        icon.setPixmap(self.create_vector_icon("bolt", "#64748b").pixmap(16, 16))
        lbl = QtWidgets.QLabel("Activity Terminal Operations Console")
        lbl.setStyleSheet("font-weight: bold; color: #64748b; font-size: 8.5pt;")
        head.addWidget(icon)
        head.addWidget(lbl)
        head.addStretch(1)
        
        clear_btn = self._button("Clear Console", self.log.clear)
        clear_btn.setObjectName("GhostBtn")
        clear_btn.setIcon(self.create_vector_icon("bolt", "#64748b"))
        clear_btn.setIconSize(QtCore.QSize(12, 12))
        clear_btn.setMinimumHeight(24)
        clear_btn.setFixedWidth(110)
        head.addWidget(clear_btn)
        layout.addLayout(head)
        layout.addWidget(self.log)
        return drawer

    def _build_config_page(self) -> None:
        self.config_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.config_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        paths = self._card("FileSystem Executables")
        paths_layout = paths.layout()
        self.maya_path = self._path_row(paths_layout, "Maya Executable", self._browse_maya)
        self.blender_path = self._path_row(paths_layout, "Blender Executable", self._browse_blender)
        self.exchange_path = self._path_row(paths_layout, "Exchange Directory", self._browse_exchange)
        layout.addWidget(paths)

        ports = self._card("Network Connection Ports")
        ports_layout = ports.layout()
        self.maya_port = QtWidgets.QSpinBox()
        self.maya_port.setRange(1024, 65535)
        self.blender_port = QtWidgets.QSpinBox()
        self.blender_port.setRange(1024, 65535)
        ports_layout.addRow("Maya Server Port", self.maya_port)
        ports_layout.addRow("Blender Server Port", self.blender_port)
        layout.addWidget(ports)

        # Setup commands completely moved to settings
        scripts_box = self._card("DCC Server Startup Commands & Scripts")
        scripts_layout = scripts_box.layout()
        
        copy_m = self._button("Copy Maya Server Script", self.copy_maya_bootstrap)
        copy_m.setIcon(self.create_vector_icon("maya", "#cbd5e1"))
        copy_m.setIconSize(QtCore.QSize(14, 14))
        
        copy_b = self._button("Copy Blender Server Script", self.copy_blender_bootstrap)
        copy_b.setIcon(self.create_vector_icon("blender", "#cbd5e1"))
        copy_b.setIconSize(QtCore.QSize(14, 14))
        
        scripts_row = QtWidgets.QHBoxLayout()
        scripts_row.setSpacing(10)
        scripts_row.addWidget(copy_m, 1)
        scripts_row.addWidget(copy_b, 1)
        scripts_layout.addRow("", scripts_row)
        layout.addWidget(scripts_box)

        save_btn = self._button("Save Settings Configurations", self.save_config, primary=True)
        save_btn.setIcon(self.create_vector_icon("settings", "#ffffff"))
        save_btn.setIconSize(QtCore.QSize(18, 18))
        save_btn.setMinimumHeight(38)
        self.apply_neon_glow(save_btn, "#2563eb", 12)
        layout.addWidget(save_btn)

        layout.addStretch(1)

    def _card(self, title: str) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(title)
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(16, 16, 16, 16)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        return box

    def _button(self, label: str, callback, primary: bool = False) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(label)
        button.setObjectName("PrimaryBtn" if primary else "GhostBtn")
        button.clicked.connect(callback)
        button.setMinimumHeight(32)
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
        """Handles visual transition states and glowing shadows for active flow buttons."""
        if self.direction == "maya":
            self.dir_maya_btn.setObjectName("FlowBtnActive")
            self.dir_blender_btn.setObjectName("FlowBtnInactive")
            self.apply_neon_glow(self.dir_maya_btn, "#38bdf8", 12)
            self.dir_blender_btn.setGraphicsEffect(None)
            
            # Subtitle explaining direction (eg: Maya export -> Blender import)
            self.flow_description_lbl.setText("Maya Export ➔ Blender Import")
            self.flow_description_lbl.setStyleSheet("font-size: 9.5pt; font-weight: 700; color: #38bdf8; letter-spacing: 0.5px;")
        else:
            self.dir_maya_btn.setObjectName("FlowBtnInactive")
            self.dir_blender_btn.setObjectName("FlowBtnActive")
            self.apply_neon_glow(self.dir_blender_btn, "#f97316", 12) # Blender Orange
            self.dir_maya_btn.setGraphicsEffect(None)
            
            # Subtitle explaining direction (eg: Blender export -> Maya import)
            self.flow_description_lbl.setText("Blender Export ➔ Maya Import")
            self.flow_description_lbl.setStyleSheet("font-size: 9.5pt; font-weight: 700; color: #f97316; letter-spacing: 0.5px;")
            
        self.dir_maya_btn.style().unpolish(self.dir_maya_btn)
        self.dir_maya_btn.style().polish(self.dir_maya_btn)
        self.dir_blender_btn.style().unpolish(self.dir_blender_btn)
        self.dir_blender_btn.style().polish(self.dir_blender_btn)

    def _on_policy_changed(self) -> None:
        if self.update_existing.isChecked():
            self._set_dot_state(self.policy_dot, True)
            if self.sync_transforms.isChecked():
                self.policy_val.setText("Update + Transform Sync")
            else:
                self.policy_val.setText("Update by Name")
        else:
            self._set_dot_state(self.policy_dot, False)
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
            
        # Clean PyInstaller environment overrides so that DCCs launch with their native Python configurations
        env = os.environ.copy()
        for key in ["PYTHONPATH", "PYTHONHOME"]:
            env.pop(key, None)
        if "PYTHONPATH_pre_pyinstaller" in env:
            env["PYTHONPATH"] = env.pop("PYTHONPATH_pre_pyinstaller")
            
        env["PORTAL_BRIDGE_ROOT"] = str(PROJECT_ROOT)
        
        # Avoid setting working directory to a temporary sys._MEIPASS path
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
            self.maya_val.setText("Connected")
        else:
            self._set_dot_state(self.blender_dot, True)
            self.blender_val.setText("Connected")

    def _copy_text(self, text: str) -> None:
        QtWidgets.QApplication.clipboard().setText(text)

    def _message(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {text}")
        self.statusBar().showMessage(text)


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setApplicationName("Portal - Maya Blender Asset Bridge (FBX)")
    
    from bridge_core.settings import PROJECT_ROOT
    portal_icon_path = PROJECT_ROOT / "icons" / "portal.png"
    if portal_icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(portal_icon_path)))
        
    window = PortalWindow()
    window.show()
    return app.exec()
