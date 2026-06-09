from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

from PyQt6 import QtCore, QtGui, QtWidgets

from bridge_core.settings import BridgeSettings, PROJECT_ROOT
from portal.styles import DARK_NEON_QSS


class BridgeWindow(QtWidgets.QDialog):
    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host = host
        self.setWindowTitle(f"Portal - {self.host.host_name.title()} Bridge")
        self.setMinimumWidth(540)
        self.setMinimumHeight(440)
        self.setStyleSheet(DARK_NEON_QSS)

        # Set gorgeous branded window icon
        window_icon = self._get_icon(self.host.host_name)
        if window_icon:
            self.setWindowIcon(window_icon)

        self._build_ui()

    def _get_icon(self, name: str) -> QtGui.QIcon:
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
        
        color = QtGui.QColor("#38bdf8" if name == "maya" else "#f97316")
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
            
        painter.end()
        return QtGui.QIcon(pixmap)

    def _apply_neon_glow(self, widget: QtWidgets.QWidget, color_hex: str = "#06b6d4", radius: int = 12) -> None:
        """Applies hardware-accelerated, high-fidelity neon drop-shadow glow to widgets."""
        effect = QtWidgets.QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(radius)
        effect.setXOffset(0)
        effect.setYOffset(0)
        effect.setColor(QtGui.QColor(color_hex))
        widget.setGraphicsEffect(effect)

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(12)

        # 1. Header with branding and host label
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(8)
        
        brand_icon = QtWidgets.QLabel("✦")
        brand_icon.setStyleSheet(f"color: {'#38bdf8' if self.host.host_name == 'maya' else '#f97316'}; font-size: 16pt; font-weight: bold;")
        title = QtWidgets.QLabel("Portal Bridge Panel")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #ffffff;")
        
        host_pill = QtWidgets.QWidget()
        host_pill.setObjectName("StatusPill")
        pill_layout = QtWidgets.QHBoxLayout(host_pill)
        pill_layout.setContentsMargins(8, 2, 8, 2)
        pill_layout.setSpacing(4)
        
        dot = QtWidgets.QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {'#38bdf8' if self.host.host_name == 'maya' else '#f97316'}; border-radius: 4px;")
        
        lbl = QtWidgets.QLabel(f"HOST: {self.host.host_name.upper()}")
        lbl.setStyleSheet("font-weight: bold; font-size: 8pt; color: #ffffff;")
        pill_layout.addWidget(dot)
        pill_layout.addWidget(lbl)
        
        header.addWidget(brand_icon)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(host_pill)
        root.addLayout(header)

        # Separator Line
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); max-height: 1px; border: none;")
        root.addWidget(sep)

        # 2. Main Transmission Deck
        deck = QtWidgets.QFrame()
        deck.setObjectName(f"{self.host.host_name.title()}Deck") # triggers deck rounded styles
        deck_layout = QtWidgets.QVBoxLayout(deck)
        deck_layout.setContentsMargins(14, 14, 14, 14)
        deck_layout.setSpacing(10)

        # Path browser
        self.path_edit = QtWidgets.QLineEdit(str(BridgeSettings().fbx_path))
        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.setObjectName("GhostBtn")
        browse_button.setFixedWidth(70)
        browse_button.clicked.connect(self._browse)
        
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.setSpacing(6)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(browse_button)
        deck_layout.addLayout(path_layout)

        # Policy Checklist Card
        policies = QtWidgets.QGroupBox("Transfer Policy Configurations")
        policies_layout = QtWidgets.QFormLayout(policies)
        policies_layout.setContentsMargins(12, 12, 12, 12)
        policies_layout.setSpacing(8)

        self.selected_only = QtWidgets.QCheckBox("Export selected mesh objects only")
        self.selected_only.setChecked(True)
        self.preserve_pivots = QtWidgets.QCheckBox("Preserve pivot coordinates & origin space offsets")
        self.preserve_pivots.setChecked(True)
        self.preserve_custom_properties = QtWidgets.QCheckBox("Preserve custom attributes / user properties")
        self.preserve_custom_properties.setChecked(True)
        self.preserve_materials = QtWidgets.QCheckBox("Preserve material slot links and assignments")
        self.preserve_materials.setChecked(True)
        self.preserve_smoothing = QtWidgets.QCheckBox("Preserve hard edges and custom smoothing groups")
        self.preserve_smoothing.setChecked(True)
        self.embed_textures = QtWidgets.QCheckBox("Embed source textures inside FBX container")

        for widget in (
            self.selected_only,
            self.preserve_pivots,
            self.preserve_custom_properties,
            self.preserve_materials,
            self.preserve_smoothing,
            self.embed_textures,
        ):
            policies_layout.addRow("", widget)
        deck_layout.addWidget(policies)

        # Core tactical operations buttons
        export_button = QtWidgets.QPushButton("Export Selection to FBX")
        export_button.setObjectName("PrimaryBtn")
        export_button.setIcon(self._get_icon("export"))
        export_button.setIconSize(QtCore.QSize(16, 16))
        export_button.setMinimumHeight(38)
        self._apply_neon_glow(export_button, "#1d4ed8" if self.host.host_name == "maya" else "#d97706", 10)

        import_button = QtWidgets.QPushButton("Import Latest FBX")
        import_button.setIcon(self._get_icon("import"))
        import_button.setIconSize(QtCore.QSize(16, 16))
        import_button.setMinimumHeight(38)
        self._apply_neon_glow(import_button, "#1d4ed8" if self.host.host_name == "maya" else "#d97706", 10)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addWidget(export_button, 1)
        button_layout.addWidget(import_button, 1)
        deck_layout.addLayout(button_layout)
        
        root.addWidget(deck, 1)

        # Clear triggers connections
        export_button.clicked.connect(lambda: self._run_action(self.host.export_selected))
        import_button.clicked.connect(lambda: self._run_action(self.host.import_fbx))

        # Bottom Status Pill
        self.status_label = QtWidgets.QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 8.5pt; font-weight: bold; color: #38bdf8;")
        root.addWidget(self.status_label)

    def _settings(self) -> BridgeSettings:
        return BridgeSettings(
            fbx_path=Path(self.path_edit.text()).expanduser(),
            selected_only=self.selected_only.isChecked(),
            preserve_pivots=self.preserve_pivots.isChecked(),
            preserve_custom_properties=self.preserve_custom_properties.isChecked(),
            preserve_materials=self.preserve_materials.isChecked(),
            preserve_smoothing=self.preserve_smoothing.isChecked(),
            embed_textures=self.embed_textures.isChecked(),
        )

    def _browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Bridge FBX Selection",
            self.path_edit.text(),
            "FBX Files (*.fbx)",
        )
        if path:
            self.path_edit.setText(path)

    def _run_action(self, action: Callable[[BridgeSettings], object]) -> None:
        self.status_label.setText("Status: Executing transmission...")
        self.status_label.setStyleSheet("color: #38bdf8; font-weight: bold;")
        QtWidgets.QApplication.processEvents()
        try:
            result = action(self._settings())
            if result and hasattr(result, "fbx_file"):
                self.path_edit.setText(str(result.fbx_file))
            mesh_count = len(result.meshes) if result and hasattr(result, "meshes") else 0
            self.status_label.setText(f"Status: Done. Active records: {mesh_count}")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
        except Exception as exc:
            self.status_label.setText(f"Status: Transmission failed: {exc}")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            QtWidgets.QMessageBox.critical(self, "Bridge Error", str(exc))


def show_window(host, parent=None):
    app = QtWidgets.QApplication.instance()
    owns_app = app is None
    if app is None:
        app = QtWidgets.QApplication([])

    window = BridgeWindow(host, parent=parent)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
    window.show()

    if owns_app:
        app.exec()
    return window
