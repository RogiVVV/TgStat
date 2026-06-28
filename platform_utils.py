import os
import platform
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog


SUPPORTED_DESKTOP_SYSTEMS = {'Windows', 'Linux', 'Darwin'}


def current_system() -> str:
    """
    Возвращает название текущей операционной системы
    :return: Windows, Linux, Darwin или другое значение platform.system()
    """
    return platform.system()


def resource_path(relative_path: str) -> str:
    """
    Возвращает путь к ресурсу приложения с учётом обычного запуска и PyInstaller-сборки
    :param relative_path: относительный путь к ресурсу
    :return: абсолютный путь к ресурсу
    """
    if hasattr(sys, '_MEIPASS'):
        return str(Path(sys._MEIPASS) / relative_path)

    return str(Path(__file__).resolve().parent / relative_path)


def first_existing_resource(*relative_paths: str) -> str:
    """
    Возвращает первый существующий ресурс из списка или первый переданный путь
    :param relative_paths: относительные пути к ресурсам
    :return: абсолютный путь к ресурсу
    """
    for relative_path in relative_paths:
        path = Path(resource_path(relative_path))
        if path.exists():
            return str(path)

    return resource_path(relative_paths[0])


def get_app_icon_path() -> str:
    """
    Возвращает путь к иконке приложения для текущей операционной системы
    :return: путь к файлу иконки
    """
    system = current_system()

    if system == 'Windows':
        return first_existing_resource('assets/icon.ico', 'assets/icon.png')

    if system == 'Darwin':
        return first_existing_resource('assets/icon.icns', 'assets/icon.png', 'assets/icon.ico')

    return first_existing_resource('assets/icon.png', 'assets/icon.ico')


def get_default_export_folder() -> Path:
    """
    Возвращает стандартную папку экспортов Telegram
    :return: путь к папке Telegram Desktop, Downloads или домашней папке
    """
    downloads_folder = Path.home() / 'Downloads'
    telegram_exports_folder = downloads_folder / 'Telegram Desktop'

    if telegram_exports_folder.exists():
        return telegram_exports_folder
    if downloads_folder.exists():
        return downloads_folder
    return Path.home()


def choose_directory(title: str, initialdir: str | Path | None = None) -> str:
    """
    Открывает системный диалог выбора папки
    :param title: заголовок окна
    :param initialdir: стартовая папка
    :return: выбранный путь или пустая строка
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askdirectory(
        title=title,
        initialdir=str(initialdir or get_default_export_folder()),
    )
    root.destroy()
    return path


def choose_json_file(title: str, initialdir: str | Path | None = None) -> str:
    """
    Открывает системный диалог выбора JSON-файла
    :param title: заголовок окна
    :param initialdir: стартовая папка
    :return: выбранный путь или пустая строка
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        title=title,
        initialdir=str(initialdir) if initialdir else None,
        filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
    )
    root.destroy()
    return path


def open_path(path: Path | str) -> None:
    """
    Открывает файл или папку стандартным средством текущей операционной системы
    :param path: путь к файлу или папке
    :return: None
    """
    target_path = Path(path)
    system = current_system()

    if system == 'Windows':
        os.startfile(str(target_path))
    elif system == 'Darwin':
        subprocess.run(['open', str(target_path)], check=False)
    else:
        subprocess.run(['xdg-open', str(target_path)], check=False)


def open_folder(folder: Path | str) -> None:
    """
    Открывает папку стандартным средством текущей операционной системы
    :param folder: путь к папке
    :return: None
    """
    folder_path = Path(folder)
    if folder_path.exists():
        open_path(folder_path)


def open_file(path: Path | str) -> None:
    """
    Открывает файл, а если это невозможно — папку, в которой он должен находиться
    :param path: путь к файлу
    :return: None
    """
    file_path = Path(path)

    try:
        if file_path.exists():
            open_path(file_path)
            return
    except Exception:
        pass

    try:
        open_folder(file_path.parent)
    except Exception:
        pass


def configure_flet_view_path() -> None:
    """
    Указывает Flet путь к локальному desktop client внутри PyInstaller-сборки.
    """
    if not is_frozen_app():
        return

    client_path = Path(resource_path('flet_client'))

    if client_path.exists():
        os.environ['FLET_VIEW_PATH'] = str(client_path)


def is_frozen_app() -> bool:
    return hasattr(sys, '_MEIPASS')
