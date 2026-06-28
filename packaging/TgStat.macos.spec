# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPEC_DIR = Path(SPECPATH).resolve() if 'SPECPATH' in globals() else Path(__file__).resolve().parent
PROJECT_ROOT = SPEC_DIR.parent if (SPEC_DIR.parent / 'app.py').exists() else SPEC_DIR


def safe_collect_data_files(package_name: str):
    try:
        return collect_data_files(package_name)
    except Exception:
        return []


def safe_collect_submodules(package_name: str):
    try:
        return collect_submodules(package_name)
    except Exception:
        return []


flet_datas = safe_collect_data_files('flet')
flet_desktop_datas = safe_collect_data_files('flet_desktop')
flet_map_datas = safe_collect_data_files('flet_map')

flet_hiddenimports = safe_collect_submodules('flet')
flet_desktop_hiddenimports = safe_collect_submodules('flet_desktop')
flet_map_hiddenimports = safe_collect_submodules('flet_map')


a = Analysis(
    [str(PROJECT_ROOT / 'app.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'assets'), 'assets'),
        *flet_datas,
        *flet_desktop_datas,
        *flet_map_datas,
    ],
    hiddenimports=[
        'regex',
        'main',
        'platform_utils',
        *flet_hiddenimports,
        *flet_desktop_hiddenimports,
        *flet_map_hiddenimports,
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

app = BUNDLE(
    coll,
    name='TgStat.app',
    icon=str(PROJECT_ROOT / 'assets' / 'icon.icns'),
    bundle_identifier='com.tgstat.app',
)