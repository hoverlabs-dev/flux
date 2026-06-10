DARK_NEON_QSS = """
/* Global Core Theme - Vercel Pure Black */
QWidget {
    background: transparent;
    color: #ededed;
    font-family: "Geist Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
    font-size: 9pt;
}

/* Central Rounded Window Container */
QWidget#CentralWidget {
    background-color: #000000;
    border: 1.5px solid #222222;
    border-radius: 20px;
}

/* Custom Title Bar */
QWidget#TitleBar {
    background: transparent;
}

QLabel#TitleBarTitle {
    background-color: #1a1a1a;
    color: #b0b0b0;
    font-size: 11pt;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 6px 24px;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

QPushButton#CloseDot {
    background-color: #ff5f56;
    border: 1.5px solid #d0433a;
    border-radius: 6px;
}

QPushButton#CloseDot:hover {
    background-color: #ff3b30;
    border: 1.5px solid #ff9b94;
}

QPushButton#MinDot {
    background-color: #ffbd2e;
    border: 1.5px solid #dca123;
    border-radius: 6px;
}

QPushButton#MinDot:hover {
    background-color: #ffcc00;
    border: 1.5px solid #ffeb99;
}

/* Typography */
QLabel#HeroTitle {
    color: #ffffff;
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: -0.5px;
}

QLabel#HeroSubtitle {
    color: #888888;
    font-size: 9pt;
}

QLabel#FlowDescription {
    color: #ffffff;
    font-size: 10pt;
    font-weight: 600;
}

/* Settings tab navigation switcher */
QWidget#NavContainer {
    background-color: #0a0a0a;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    padding: 2px;
}

QPushButton#NavBtnActive {
    background-color: #1f1f1f;
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 14px;
    min-height: 24px;
}

QPushButton#NavBtnInactive {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #888888;
    font-weight: 500;
    padding: 6px 14px;
    min-height: 24px;
}

QPushButton#NavBtnInactive:hover {
    color: #ffffff;
    background-color: #141414;
}

/* Segmented Control */
QWidget#SegmentContainer {
    background-color: #0a0a0a;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    padding: 3px;
}

QPushButton#SegmentActive {
    background-color: #1f1f1f;
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
    min-height: 28px;
}

QPushButton#SegmentInactive {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #888888;
    font-weight: 500;
    padding: 8px 16px;
    min-height: 28px;
}

QPushButton#SegmentInactive:hover {
    color: #ffffff;
    background-color: #141414;
}

/* Card Deck for configurations */
QFrame#ControlHubFrame, QGroupBox {
    background-color: #0a0a0a;
    border: 1px solid #1f1f1f;
    border-radius: 12px;
    padding: 10px;
}

QGroupBox {
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 4px;
    color: #ffffff;
}

/* Inputs & Form Controls */
QLineEdit, QSpinBox {
    background-color: #000000;
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    color: #ffffff;
    min-height: 28px;
    padding: 2px 8px;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #444444;
}

/* Buttons */
QPushButton {
    background-color: transparent;
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 500;
    padding: 6px 12px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #1a1a1a;
    border: 1px solid #555555;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1a1a1a;
}

QPushButton#PrimaryBtn {
    background-color: #ffffff;
    border: 1px solid #ffffff;
    color: #000000;
    font-weight: 700;
}

QPushButton#PrimaryBtn:hover {
    background-color: #ececec;
    border: 1px solid #ececec;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #dcdcdc;
}

QPushButton#GhostBtn {
    background-color: transparent;
    border: 1px solid #1f1f1f;
}

QPushButton#GhostBtn:hover {
    background-color: #161616;
    border: 1px solid #444444;
    color: #ffffff;
}

QPushButton#CollapseToggleBtn {
    background-color: transparent;
    border: none;
    color: #666666;
    font-size: 8.5pt;
    font-weight: 600;
}

QPushButton#CollapseToggleBtn:hover {
    color: #ffffff;
}

/* Custom Checkboxes */
QCheckBox {
    color: #888888;
    spacing: 8px;
    font-size: 8.5pt;
}

QCheckBox:hover {
    color: #ffffff;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #333333;
    background-color: #000000;
}

QCheckBox::indicator:hover {
    border: 1px solid #444444;
}

QCheckBox::indicator:checked {
    border: 1px solid #ffffff;
    background-color: #ffffff;
}

/* Status indicator pills */
QWidget#StatusPill {
    background-color: #0a0a0a;
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    padding: 2px 8px;
}

QLabel#StatusLabel {
    color: #666666;
    font-weight: 600;
    font-size: 8pt;
}

QLabel#StatusText {
    color: #ffffff;
    font-weight: 600;
    font-size: 8pt;
}

QLabel#PathLabel {
    color: #888888;
    font-family: "Geist Mono", monospace;
    font-size: 8pt;
}

/* Console Drawer */
QPlainTextEdit {
    background-color: #000000;
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    color: #a3a3a3;
    font-family: "Geist Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
    font-size: 8pt;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
}

QScrollBar::handle:vertical {
    background: #222222;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #333333;
}
"""
