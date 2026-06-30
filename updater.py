import json
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from packaging.version import InvalidVersion, Version

import platform_utils

GITHUB_REPO = 'RogiVVV/TgStat'
GITHUB_RELEASES_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
GITHUB_RELEASES_URL = f'https://github.com/{GITHUB_REPO}/releases/latest'
REQUEST_TIMEOUT = 12


@dataclass(frozen=True)
class UpdateInfo:
    """
    Описывает найденное обновление приложения.
    """
    current_version: str
    latest_version: str
    release_name: str
    release_notes: str
    page_url: str
    asset_name: str | None
    asset_url: str | None


@dataclass(frozen=True)
class PreparedUpdate:
    """
    Описывает подготовленное обновление, которое осталось применить скриптом.
    """
    script_path: Path
    update_folder: Path


def normalize_version(version: str) -> Version:
    """
    Преобразует строку версии в объект Version.
    :param version: версия вида v1.2.3, 1.2.3, 0.2b1
    :return: объект версии
    """
    cleaned = version.strip().lower()
    if cleaned.startswith('v'):
        cleaned = cleaned[1:]

    cleaned = cleaned.replace('-beta.', 'b')
    cleaned = cleaned.replace('-beta', 'b')
    cleaned = cleaned.replace('-rc.', 'rc')
    cleaned = cleaned.replace('-rc', 'rc')
    cleaned = cleaned.replace('-alpha.', 'a')
    cleaned = cleaned.replace('-alpha', 'a')

    return Version(cleaned)


def is_newer_version(latest_version: str, current_version: str) -> bool:
    """
    Проверяет, новее ли latest_version текущей версии.
    :param latest_version: версия из релиза
    :param current_version: версия приложения
    :return: True, если доступна новая версия
    """
    try:
        return normalize_version(latest_version) > normalize_version(current_version)
    except InvalidVersion:
        return latest_version.strip().lower() != current_version.strip().lower()


def request_json(url: str) -> dict[str, Any]:
    """
    Загружает JSON по URL.
    :param url: адрес API
    :return: словарь ответа
    """
    request = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'TgStat updater',
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode('utf-8'))


def platform_asset_keywords() -> list[str]:
    """
    Возвращает ключевые слова для поиска архива под текущую ОС.
    :return: список ключевых слов
    """
    system = platform_utils.current_system()
    if system == 'Windows':
        return ['windows', 'win']
    if system == 'Darwin':
        return ['macos', 'mac', 'darwin']
    if system == 'Linux':
        return ['linux']
    return [system.lower()]


def select_release_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Выбирает подходящий ZIP-архив из GitHub Release для текущей ОС.
    :param assets: список assets из GitHub API
    :return: asset или None
    """
    keywords = platform_asset_keywords()
    archive_assets = [
        asset for asset in assets
        if str(asset.get('name', '')).lower().endswith(('.zip', '.tar.gz', '.tgz'))
    ]

    for asset in archive_assets:
        name = str(asset.get('name', '')).lower()
        if any(keyword in name for keyword in keywords):
            return asset

    return archive_assets[0] if len(archive_assets) == 1 else None


def check_for_update(current_version: str) -> UpdateInfo | None:
    """
    Проверяет наличие новой версии в GitHub Releases.
    :param current_version: текущая версия приложения
    :return: информация об обновлении или None
    """
    try:
        release = request_json(GITHUB_RELEASES_API_URL)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    latest_version = str(release.get('tag_name') or '').strip()
    if not latest_version or not is_newer_version(latest_version, current_version):
        return None

    asset = select_release_asset(release.get('assets') or [])
    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        release_name=str(release.get('name') or latest_version),
        release_notes=str(release.get('body') or ''),
        page_url=str(release.get('html_url') or GITHUB_RELEASES_URL),
        asset_name=str(asset.get('name')) if asset else None,
        asset_url=str(asset.get('browser_download_url')) if asset else None,
    )


def download_file(url: str, output_path: Path) -> None:
    """
    Скачивает файл по URL.
    :param url: адрес файла
    :param output_path: путь сохранения
    :return: None
    """
    request = urllib.request.Request(url, headers={'User-Agent': 'TgStat updater'})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        with open(output_path, 'wb') as file:
            shutil.copyfileobj(response, file)


def unpack_archive(archive_path: Path, output_folder: Path) -> None:
    """
    Распаковывает архив обновления.
    :param archive_path: путь к архиву
    :param output_folder: папка распаковки
    :return: None
    """
    archive_name = archive_path.name.lower()
    if archive_name.endswith('.zip'):
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(output_folder)
        return

    shutil.unpack_archive(str(archive_path), str(output_folder))


def find_update_root(unpack_folder: Path) -> Path:
    """
    Находит корневую папку приложения внутри распакованного архива.
    :param unpack_folder: папка распаковки
    :return: папка с файлами новой версии
    """
    children = [path for path in unpack_folder.iterdir() if path.name not in {'__MACOSX'}]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return unpack_folder


def get_install_folder() -> Path:
    """
    Возвращает папку установленного приложения.
    :return: путь к папке приложения
    """
    if platform_utils.is_frozen_app():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_executable_path() -> Path:
    """
    Возвращает путь к исполняемому файлу текущего приложения.
    :return: путь к exe/app или python-файлу
    """
    if platform_utils.is_frozen_app():
        return Path(sys.executable).resolve()
    return Path(__file__).resolve().parent / 'app.py'


def make_windows_update_script(update_root: Path, install_folder: Path, executable_path: Path) -> Path:
    """
    Создаёт PowerShell-скрипт для применения обновления на Windows.
    :param update_root: папка с новой версией
    :param install_folder: папка установленного приложения
    :param executable_path: путь к исполняемому файлу
    :return: путь к скрипту
    """
    script_path = update_root.parent / 'apply_update.ps1'
    script = f'''
Start-Sleep -Seconds 2
$Source = {json.dumps(str(update_root))}
$Target = {json.dumps(str(install_folder))}
$Exe = {json.dumps(str(executable_path))}
Copy-Item -Path (Join-Path $Source '*') -Destination $Target -Recurse -Force
Start-Process -FilePath $Exe
'''.strip()
    script_path.write_text(script, encoding='utf-8')
    return script_path


def make_unix_update_script(update_root: Path, install_folder: Path, executable_path: Path) -> Path:
    """
    Создаёт shell-скрипт для применения обновления на Linux/macOS.
    :param update_root: папка с новой версией
    :param install_folder: папка установленного приложения
    :param executable_path: путь к исполняемому файлу
    :return: путь к скрипту
    """
    script_path = update_root.parent / 'apply_update.sh'
    script = f'''#!/bin/sh
            sleep 2
            cp -R {sh_quote(str(update_root))}/. {sh_quote(str(install_folder))}/
            chmod +x {sh_quote(str(executable_path))} 2>/dev/null || true
            {sh_quote(str(executable_path))} >/dev/null 2>&1 &
            '''
    script_path.write_text(script, encoding='utf-8')
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


def sh_quote(value: str) -> str:
    """
    Экранирует строку для shell.
    :param value: исходная строка
    :return: безопасная строка
    """
    return "'" + value.replace("'", "'\\''") + "'"


def prepare_update(update_info: UpdateInfo) -> PreparedUpdate:
    """
    Скачивает обновление, распаковывает его и создаёт скрипт применения.
    :param update_info: информация об обновлении
    :return: подготовленное обновление
    """
    if not is_auto_update_supported():
        raise RuntimeError('Автообновление доступно только в собранной версии приложения')

    if not update_info.asset_url or not update_info.asset_name:
        raise RuntimeError('Для текущей системы не найден архив обновления')

    temp_root = Path(tempfile.mkdtemp(prefix='tgstat_update_'))
    archive_path = temp_root / update_info.asset_name
    unpack_folder = temp_root / 'new_version'
    unpack_folder.mkdir(parents=True, exist_ok=True)

    download_file(update_info.asset_url, archive_path)
    unpack_archive(archive_path, unpack_folder)

    update_root = find_update_root(unpack_folder)
    install_folder = get_install_folder()
    executable_path = get_executable_path()

    if platform_utils.current_system() == 'Windows':
        script_path = make_windows_update_script(update_root, install_folder, executable_path)
    else:
        script_path = make_unix_update_script(update_root, install_folder, executable_path)

    return PreparedUpdate(script_path=script_path, update_folder=temp_root)


def run_prepared_update(prepared_update: PreparedUpdate) -> None:
    """
    Запускает скрипт обновления.
    :param prepared_update: подготовленное обновление
    :return: None
    """
    if platform_utils.current_system() == 'Windows':
        subprocess.Popen([
            'powershell',
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-File',
            str(prepared_update.script_path),
        ], close_fds=True)
    else:
        subprocess.Popen([str(prepared_update.script_path)], close_fds=True)

    time.sleep(0.2)


def is_auto_update_supported() -> bool:
    """
    Проверяет, можно ли безопасно применять автообновление.
    :return: True для собранного приложения
    """
    return platform_utils.is_frozen_app()
