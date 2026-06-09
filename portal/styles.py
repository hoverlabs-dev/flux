DARK_NEON_QSS = """
/* Global Core Theme - Frosted Obsidian Sapphire & Violet */
QWidget {
    background: #060911;
    color: #e2e8f0;
    font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
    font-size: 10pt;
}

QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #05070f, stop:1 #0b0f1d);
}

/* Typography & Hero Banner */
QLabel#HeroTitle {
    color: #ffffff;
    font-size: 24pt;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#HeroSubtitle {
    color: #94a3b8;
    font-size: 9.5pt;
    font-weight: 500;
}

/* Custom DCC Connection Indicators & Status Pills */
QWidget#StatusPill {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 2px 10px;
}

QLabel#StatusLabel {
    color: #64748b;
    font-weight: 700;
    font-size: 8.5pt;
}

QLabel#StatusText {
    color: #f1f5f9;
    font-weight: 600;
    font-size: 8.5pt;
}

QLabel#PathLabel {
    color: #38bdf8;
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 8.5pt;
    font-weight: 600;
}

/* DCC Interactive Cards - Reimagined Launchpad */
QFrame#DccCardMaya {
    background: rgba(13, 20, 30, 0.4);
    border: 1px solid rgba(56, 189, 248, 0.12);
    border-radius: 16px;
}

QFrame#DccCardMaya:hover {
    background: rgba(13, 20, 30, 0.6);
    border: 1px solid rgba(56, 189, 248, 0.35);
}

QFrame#DccCardBlender {
    background: rgba(13, 20, 30, 0.4);
    border: 1px solid rgba(249, 115, 22, 0.12);
    border-radius: 16px;
}

QFrame#DccCardBlender:hover {
    background: rgba(13, 20, 30, 0.6);
    border: 1px solid rgba(249, 115, 22, 0.35);
}

/* DCC View Decks for backward compatibility */
QFrame#MayaDeck {
    background: rgba(13, 20, 30, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

QFrame#BlenderDeck {
    background: rgba(13, 20, 30, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

/* Reimagined Centralized Bridge Control Hub Frame */
QFrame#ControlHubFrame {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
}

QWidget#TransContainer {
    background: transparent;
    border: none;
}

/* Premium Containers / Settings Cards */
QGroupBox {
    background: rgba(15, 23, 42, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    margin-top: 18px;
    padding-top: 18px;
    font-weight: 700;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    color: #38bdf8;
    font-size: 9.5pt;
}

QFormLayout > QLabel {
    color: #64748b;
    font-weight: 700;
    font-size: 8.5pt;
    text-transform: uppercase;
}

/* Form Controls & Inputs - Frosty Glass */
QLineEdit, QSpinBox, QComboBox {
    background: rgba(4, 6, 10, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: #f1f5f9;
    min-height: 32px;
    padding: 2px 10px;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid rgba(56, 189, 248, 0.6);
    background: rgba(8, 12, 20, 0.85);
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left-width: 0px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

/* Buttons - Premium Interactive Glass Plate */
QPushButton {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: #cbd5e1;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 9.5pt;
    min-height: 20px;
}

QPushButton:hover {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.5);
    color: #ffffff;
}

QPushButton:pressed {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(37, 99, 235, 0.6);
}

QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(37, 99, 235, 0.85), stop:1 rgba(29, 78, 216, 0.85));
    border: 1px solid rgba(56, 189, 248, 0.6);
    color: #ffffff;
    font-weight: 700;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(59, 130, 246, 0.9), stop:1 rgba(37, 99, 235, 0.9));
    border: 1px solid rgba(14, 165, 233, 0.8);
}

QPushButton#GhostBtn {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
}

QPushButton#GhostBtn:hover {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(56, 189, 248, 0.6);
}

/* Custom Collapsible Button (Toggle link) */
QPushButton#CollapseToggleBtn {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 8.5pt;
    font-weight: 700;
    padding: 4px;
}

QPushButton#CollapseToggleBtn:hover {
    color: #38bdf8;
}

/* Top Navigation Buttons */
QPushButton#NavBtnActive {
    background: rgba(30, 58, 138, 0.35);
    border: 2px solid rgba(56, 189, 248, 0.6);
    border-radius: 8px;
    color: #38bdf8;
    padding: 6px 16px;
    font-weight: 700;
}

QPushButton#NavBtnInactive {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    color: #64748b;
    padding: 6px 16px;
    font-weight: 600;
}

QPushButton#NavBtnInactive:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

/* Active & Inactive Flow Buttons */
QPushButton#FlowBtnActive {
    background: rgba(30, 58, 138, 0.45);
    border: 2px solid rgba(56, 189, 248, 0.6);
    border-radius: 10px;
    color: #38bdf8;
    padding: 8px 16px;
    font-weight: 800;
    font-size: 11pt;
}

QPushButton#FlowBtnActive:hover {
    background: rgba(30, 58, 138, 0.6);
}

QPushButton#FlowBtnInactive {
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    color: #64748b;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 10.5pt;
}

QPushButton#FlowBtnInactive:hover {
    background: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Custom Checkboxes */
QCheckBox {
    color: #94a3b8;
    spacing: 8px;
    font-weight: 500;
    font-size: 9pt;
}

QCheckBox:hover {
    color: #cbd5e1;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #334155;
    background: rgba(4, 6, 10, 0.6);
}

QCheckBox::indicator:hover {
    border: 2px solid rgba(56, 189, 248, 0.6);
    background: rgba(10, 15, 22, 0.8);
}

QCheckBox::indicator:checked {
    border: 2px solid #2563eb;
    background: #2563eb;
}

/* Developer PlainText Logger Console */
QPlainTextEdit {
    background: rgba(3, 5, 10, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    color: #cbd5e1;
    padding: 8px;
    font-family: "Cascadia Mono", Consolas, "JetBrains Mono", monospace;
    font-size: 9pt;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Accent Status Bar */
QStatusBar {
    background: #05070d;
    color: #38bdf8;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 8.5pt;
    font-weight: 600;
}
"""
