# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

project_dir = Path.cwd()

flet_datas = collect_data_files('flet')
flet_map_datas = collect_data_files('flet_map')


a = Analysis(
    ['app.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        *flet_datas,
        *flet_map_datas,
    ],
    hiddenimports=[
        'flet',
        'flet_map',
        'regex',
        'main',
        'platform_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TgStat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TgStat',
)
