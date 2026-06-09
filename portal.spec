# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Dynamic resolution of the vendored PyQt6 runtime path matching the current Python version
py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
vendored_path = str(Path('vendor') / 'python' / py_tag)

block_cipher = None

a = Analysis(
    ['run_portal.py'],
    pathex=[vendored_path],
    binaries=[],
    datas=[
        ('icons', 'icons'),
        ('hosts', 'hosts'),
        ('portal_dcc', 'portal_dcc'),
        ('bridge_core', 'bridge_core'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Portal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/portal.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Portal'
)
