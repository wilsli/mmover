# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mmover.py'],
    pathex=[],
    binaries=[('/Users/wilson/TrenzCloud/Xchange/mmover/ffmpeg/ffprobe', './ffmpeg')],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pip', 'setuptools', 'wheel'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mmover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
