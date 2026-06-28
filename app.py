import asyncio
import json
from collections import Counter
from pathlib import Path
from typing import Any
import datetime

import flet as ft

try:
    import flet_map as ftm
except ImportError:
    ftm = None

import main as chat_backend
import platform_utils

TOP_LIMIT = 10

STAT_GROUPS = [
    (
        'user_activity',
        'Топ пользователей по:',
        [
            ('count_msgs_by_user', 'сообщениям'),
            ('count_total_reactions_by_user', 'реакциям'),
            ('count_photos_by_user', 'фото'),
            ('count_videos_by_user', 'видео'),
            ('count_stickers_by_user', 'стикерам'),
            ('count_files_by_user', 'файлам'),
            ('count_voice_msgs_by_user', 'голосовым сообщениям'),
            ('count_video_msgs_by_user', 'видеосообщениям'),
            ('count_gifs_by_user', 'GIF'),
            ('count_audios_by_user', 'аудио'),
            ('count_smiles_by_user', 'улыбочкам)'),
            ('count_locations_by_user', 'геолокациям'),
            ('count_contacts_by_user', 'контактам'),
            ('count_polls_by_user', 'опросам'),
            ('count_edited_by_user', 'изменению сообщений'),
            ('count_forwarded_by_user', 'пересылке сообщений'),
            ('count_replies_by_user', 'ответам'),
        ],
    ),
    (
        'user_cards',
        'Карточки пользователей:',
        [
            ('users_stats', 'Карточки пользователей'),
        ],
    ),
    (
        'text',
        'Текстовые статистики:',
        [
            ('count_words_by_user', 'Топ слов'),
            ('count_letters_by_user', 'Топ букв'),
            ('count_digits_by_user', 'Топ цифр'),
            ('count_emojis_by_user', 'Топ эмодзи'),
            ('count_laugh', 'Топ смеха'),
            ('count_text_types', 'Типы текста'),
            ('programming_languages_count', 'Языки программирования'),
            ('custom_phrases_count_by_user', 'Кастомные фразы'),
            ('longest_msg', 'Самые длинные сообщения'),
        ],
    ),
    (
        'reactions_replies',
        'Реакции и ответы:',
        [
            ('count_reactions_by_user', 'Топ реакций'),
            ('most_reacted', 'Самые залайканные сообщения'),
            ('msgs_by_replies_count', 'Сообщения, на которые чаще всего отвечали'),
        ],
    ),
    (
        'files_media',
        'Файлы и медиа:',
        [
            ('max_file_size', 'Самые большие файлы'),
            ('longest_voice_msg', 'Самые длинные голосовые сообщения'),
            ('longest_video_msg', 'Самые длинные видеосообщения'),
            ('longest_video', 'Самые длинные видео'),
            ('longest_audio', 'Самые длинные аудио'),
            ('longest_gif', 'Самые длинные GIF'),
            ('count_stickers', 'Топ стикеров'),
        ],
    ),
    (
        'other',
        'Прочее:',
        [
            ('count_by_day', 'Сообщения по дням'),
            ('service_action_dict', 'Сервисные действия'),
            ('forwarded_from_count', 'Откуда пересылали'),
            ('count_via_by_user', 'Сообщения через ботов'),
            ('locations', 'Карта геопозиций'),
        ],
    ),
]

ALL_STAT_KEYS = sorted({stat_key for _, _, items in STAT_GROUPS for stat_key, _ in items})
PREVIEW_STAT_KEYS = {
    'most_reacted',
    'msgs_by_replies_count',
    'max_file_size',
    'longest_voice_msg',
    'longest_video_msg',
    'longest_video',
    'longest_audio',
    'longest_gif',
    'count_stickers',
    'longest_msg',
}

APP_BG = '#0F1117'
CARD_BG = '#181B22'
CARD_BG_2 = '#20242D'
CARD_BG_3 = '#252A35'
ACCENT = '#2AABEE'
DISCORD = '#5865F2'
TEXT = '#F4F7FB'
TEXT_MUTED = '#9AA4B2'
BORDER = '#303746'
SUCCESS = '#2ECC71'
WARNING = '#E74C3C'
RESULT_CARD_BG = '#242936'
RESULT_CARD_BG_2 = '#2D3443'
RESULT_CARD_BG_3 = '#374052'
LINK_COLOR = '#5C9CCF'
SAVED_ANALYZES_DIR = Path(__file__).resolve().parent / 'saved_analyzes'
ABOUT_URL = 'https://github.com/RogiVVV/TgStat'



def make_page_shell(content: ft.Control, max_width: int = 1180) -> ft.Container:
    """
    Создаёт общий контейнер страницы
    :param content: содержимое страницы
    :param max_width: максимальная ширина содержимого
    :return: контейнер Flet
    """
    return ft.Container(
        content=ft.Container(
            content=content,
            width=max_width,
            padding=ft.Padding(left=24, top=28, right=24, bottom=28),
        ),
        alignment=ft.Alignment(0, -1),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[APP_BG, '#111827', '#0B1020'],
        ),
    )


def make_card(content: ft.Control, padding: int = 22, bgcolor: str = CARD_BG) -> ft.Container:
    """
    Создаёт декоративную карточку
    :param content: содержимое карточки
    :param padding: внутренний отступ
    :param bgcolor: цвет фона
    :return: контейнер Flet
    """
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=24,
        bgcolor=bgcolor,
        border=ft.Border(
            left=ft.BorderSide(1, BORDER),
            top=ft.BorderSide(1, BORDER),
            right=ft.BorderSide(1, BORDER),
            bottom=ft.BorderSide(1, BORDER),
        ),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=22,
            color='#33000000',
            offset=ft.Offset(0, 10),
        ),
    )


def make_primary_button(text: str, on_click: Any | None = None, disabled: bool = False) -> ft.Button:
    """
    Создаёт основную кнопку приложения
    :param text: текст кнопки
    :param on_click: обработчик клика
    :param disabled: заблокирована ли кнопка
    :return: кнопка Flet
    """
    return ft.Button(
        text,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=TEXT,
            bgcolor=ACCENT,
            padding=ft.Padding(left=22, top=14, right=22, bottom=14),
            shape=ft.RoundedRectangleBorder(radius=14),
        ),
    )


def make_secondary_button(text: str, on_click: Any | None = None) -> ft.Button:
    """
    Создаёт вторичную кнопку приложения
    :param text: текст кнопки
    :param on_click: обработчик клика
    :return: кнопка Flet
    """
    return ft.Button(
        text,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=TEXT,
            bgcolor=CARD_BG_2,
            padding=ft.Padding(left=18, top=13, right=18, bottom=13),
            shape=ft.RoundedRectangleBorder(radius=14),
            side=ft.BorderSide(1, BORDER),
        ),
    )


def sanitize_filename_part(value: Any) -> str:
    """
    Очищает часть имени файла от недопустимых символов
    :param value: исходное значение
    :return: безопасная строка для имени файла
    """
    result = ''.join(symbol if symbol.isalnum() or symbol in {'-', '_'} else '_' for symbol in str(value).strip())
    return result.strip('_') or 'chat'


def make_json_safe(value: Any) -> Any:
    """
    Преобразует статистику в JSON-совместимый формат
    :param value: исходное значение
    :return: JSON-совместимое значение
    """
    if isinstance(value, Counter):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def save_analysis_to_json(stats: dict, folder: str) -> Path:
    """
    Сохраняет результаты анализа в отдельный JSON-файл
    :param stats: словарь статистик
    :param folder: папка для сохранения
    :return: путь к сохранённому файлу
    """
    output_folder = Path(folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    analysis_name = stats.get('_analysis_name')
    chat_type = sanitize_filename_part(stats.get('_chat_type', 'chat'))
    chat_name = sanitize_filename_part(stats.get('_chat_name', 'telegram'))
    if analysis_name:
        filename = f'{sanitize_filename_part(analysis_name)}.json'
    else:
        filename = f'TgStat_{chat_type}_{chat_name}.json'
    output_path = output_folder / filename
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(make_json_safe(stats), file, ensure_ascii=False, indent=2)
    return output_path


def get_saved_analyzes_folder() -> Path:
    """
    Возвращает папку приложения для сохранённых анализов и создаёт её при необходимости
    :return: путь к папке saved_analyzes
    """
    SAVED_ANALYZES_DIR.mkdir(parents=True, exist_ok=True)
    return SAVED_ANALYZES_DIR


def read_analysis_from_json(path: str | Path) -> dict:
    """
    Читает сохранённый анализ из JSON-файла
    :param path: путь к JSON-файлу
    :return: словарь со статистикой
    """
    with open(path, 'r', encoding='utf-8') as file:
        stats = json.load(file)
    stats.setdefault('_message_previews', {'texts': {}, 'files': {}, 'sticker_files': {}})
    stats.setdefault('_selected_statistics', [key for key in stats if key in ALL_STAT_KEYS])
    return stats



def read_chat_meta(chat_path: str) -> dict[str, str]:
    """
    Читает название и тип Telegram-чата из result.json
    :param chat_path: путь к папке экспорта Telegram
    :return: словарь с названием и типом чата
    """
    result_path = Path(chat_path) / 'result.json'
    with open(result_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return {
        'name': str(data.get('name') or 'Без названия'),
        'type': str(data.get('type') or 'chat'),
    }


def chat_type_label(chat_type: str | None) -> str:
    """
    Возвращает русское название типа Telegram-сущности
    :param chat_type: тип из result.json
    :return: человекочитаемый тип
    """
    labels = {
        'personal_chat': 'личного чата c',
        'private_group': 'группы',
        'public_group': 'группы',
        'private_supergroup': 'группы',
        'public_supergroup': 'группы',
        'private_channel': 'канала',
        'public_channel': 'канала',
        'saved_messages': 'избранного',
    }
    return labels.get(str(chat_type), 'чата/канала/группы')



def user_name(user_id: str | None, users: dict) -> str:
    """
    Возвращает имя пользователя по его id
    :param user_id: id пользователя
    :param users: словарь пользователей
    :return: имя пользователя
    """
    if user_id is None:
        return 'Unknown'
    return users.get(user_id, 'Unknown')


def parse_custom_phrases(raw_text: str) -> list[str]:
    """
    Преобразует текстовое поле в список кастомных фраз
    :param raw_text: текст из поля ввода
    :return: список кастомных фраз
    """
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def sorted_counter_items(counter: Counter | dict, limit: int | None = None) -> list[tuple[Any, int]]:
    """
    Возвращает отсортированные элементы Counter или обычного словаря
    :param counter: исходная статистика
    :param limit: максимальное количество элементов
    :return: список элементов
    """
    if hasattr(counter, 'most_common'):
        rows = counter.most_common()
    else:
        rows = list(counter.items())
        rows.sort(key=lambda row: row[1], reverse=True)
    if limit is None:
        return rows
    return rows[:limit]


def counter_without_total(counter: Counter | dict) -> list[tuple[Any, int]]:
    """
    Возвращает элементы счётчика без значения total
    :param counter: исходный счётчик
    :return: список элементов счётчика
    """
    return [
        (key, value)
        for key, value in sorted_counter_items(counter)
        if key != 'total'
    ]


def top_from_info_counter(counter: Counter | dict, limit: int | None = TOP_LIMIT) -> list[tuple[Any, int]]:
    """
    Возвращает топ элементов из простого счётчика
    :param counter: исходный счётчик
    :param limit: максимальное количество элементов
    :return: список элементов топа
    """
    return sorted_counter_items(counter, limit)


def top_from_nested_counter(data: dict, limit: int | None = TOP_LIMIT) -> list[tuple[Any, int, list[tuple[Any, int]]]]:
    """
    Возвращает топ элементов из вложенной статистики
    :param data: словарь со статистикой вида объект -> пользователь -> количество
    :param limit: максимальное количество элементов
    :return: список элементов топа с общей суммой и детализацией
    """
    rows = []
    for item, counter in data.items():
        total = counter.get('total', 0)
        details = counter_without_total(counter)
        rows.append((item, total, details))
    rows.sort(key=lambda row: row[1], reverse=True)
    if limit is None:
        return rows
    return rows[:limit]


def extract_message_text(msg: dict) -> str:
    """
    Извлекает текст сообщения из json-структуры Telegram
    :param msg: сообщение в формате json
    :return: текст сообщения
    """
    text_entities = msg.get('text_entities') or []
    if text_entities:
        return ''.join(entity.get('text') or '' for entity in text_entities).strip()

    text = msg.get('text')
    if isinstance(text, str):
        return text.strip()
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get('text') or '')
        return ''.join(parts).strip()

    return ''


def get_message_file_path(msg: dict, chat_path: str) -> Path | None:
    """
    Возвращает путь к файлу сообщения
    :param msg: сообщение в формате json
    :param chat_path: путь к папке экспорта Telegram
    :return: путь к файлу или None
    """
    file_path = msg.get('file') or msg.get('photo')
    if not file_path:
        return None

    full_path = Path(chat_path) / file_path
    if full_path.exists():
        return full_path

    return None


def collect_message_previews(chat_path: str) -> dict[str, dict[int, Any]]:
    """
    Собирает тексты сообщений и пути к файлам для предпросмотра
    :param chat_path: путь к папке экспорта Telegram
    :return: словарь с текстами сообщений и путями к файлам
    """
    result_path = Path(chat_path) / 'result.json'
    with open(result_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    texts = {}
    files = {}
    sticker_files = {}

    for msg in data.get('messages', []):
        msg_id = msg.get('id')
        if msg_id is None or msg.get('type') != 'message':
            continue

        text = extract_message_text(msg)
        if text:
            texts[msg_id] = text

        file_path = get_message_file_path(msg, chat_path)
        if file_path:
            files[msg_id] = file_path
            if msg.get('media_type') == 'sticker' and msg.get('file'):
                sticker_files[msg.get('file')] = file_path

    return {
        'texts': texts,
        'files': files,
        'sticker_files': sticker_files,
    }


def shorten_text(text: str, limit: int = 180) -> str:
    """
    Сокращает текст для отображения в интерфейсе
    :param text: исходный текст
    :param limit: максимальная длина текста
    :return: сокращённый текст
    """
    text = ' '.join(text.split())
    if len(text) <= limit:
        return text
    return f'{text[:limit - 1]}…'


def format_value(value: Any, unit: str | None = None) -> str:
    """
    Форматирует значение с единицей измерения
    :param value: значение
    :param unit: единица измерения
    :return: строка со значением и единицей измерения
    """
    if unit:
        return f'{value} {unit}'
    return str(value)


def user_details_text(details: list[tuple[Any, int]], users: dict, limit: int | None = None) -> str:
    """
    Формирует текст детализации статистики по пользователям
    :param details: список пар user_id -> count
    :param users: словарь пользователей
    :param limit: максимальное количество пользователей
    :return: строка детализации
    """
    visible_details = details if limit is None else details[:limit]
    return ', '.join(
        f'{user_name(user_id, users)}: {count}'
        for user_id, count in visible_details
    )



def make_show_more_button(
        rows: list[Any],
        visible_count: int,
        render_rows: Any,
        button_holder: ft.Column,
        page: ft.Page | None = None
) -> ft.Button | None:
    """
    Создаёт кнопку для показа следующих строк топа
    :param rows: все строки топа
    :param visible_count: текущее количество видимых строк
    :param render_rows: функция перерисовки строк
    :param button_holder: контейнер для кнопки
    :param page: страница Flet
    :return: кнопка Flet или None
    """
    if visible_count >= len(rows):
        return None

    def show_more(_: ft.ControlEvent) -> None:
        next_count = visible_count + TOP_LIMIT
        render_rows(next_count)
        if page:
            page.update()

    return ft.Button('Показать больше', on_click=show_more)


def make_message_or_file_control(item: Any, previews: dict[str, dict[int, Any]]) -> ft.Control:
    """
    Создаёт элемент интерфейса для сообщения или файла
    :param item: идентификатор сообщения или файла
    :param previews: словарь предпросмотров
    :return: элемент интерфейса Flet
    """
    texts: dict[Any, Any] = previews['texts']
    files: dict[Any, Any] = previews['files']

    text = texts.get(item) or texts.get(str(item))
    file_path = files.get(item) or files.get(str(item))
    controls = []

    if text:
        controls.append(ft.Text(shorten_text(text), expand=True, selectable=True))

    if file_path:
        file_path = Path(file_path)
        controls.append(
            ft.TextButton(
                file_path.name,
                on_click=lambda e, p=file_path: platform_utils.open_file(p)
            )
        )

    if controls:
        return ft.Column(controls=controls, spacing=2, expand=True)

    return ft.Text(f'message id: {item}', expand=True)


def make_file_control(item: Any, previews: dict[str, dict[int, Any]]) -> ft.Control:
    """
    Создаёт элемент интерфейса для файла сообщения
    :param item: идентификатор сообщения
    :param previews: словарь предпросмотров
    :return: элемент интерфейса Flet
    """
    files: dict[Any, Any] = previews['files']

    file_path = files.get(item) or files.get(str(item))
    if file_path:
        file_path = Path(file_path)
        return ft.TextButton(
            file_path.name,
            on_click=lambda e, p=file_path: platform_utils.open_file(p)
        )

    return ft.Text(f'message id: {item}', expand=True)


def make_sticker_control(item: Any, previews: dict[str, dict[int, Any]]) -> ft.Control:
    """
    Создаёт элемент интерфейса для стикера
    :param item: путь к стикеру из result.json
    :param previews: словарь предпросмотров
    :return: элемент интерфейса Flet
    """
    sticker_files: dict[Any, Any] = previews.get('sticker_files', {})

    sticker_path = sticker_files.get(item) or sticker_files.get(str(item))
    if not sticker_path:
        return ft.Text(str(item), expand=True, selectable=True)

    controls = []
    sticker_path = Path(sticker_path)
    if sticker_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        controls.append(
            ft.Image(
                src=str(sticker_path),
                width=72,
                height=72,
            )
        )

    controls.append(
        ft.TextButton(
            sticker_path.name,
            on_click=lambda e, p=sticker_path: platform_utils.open_file(p)
        )
    )

    return ft.Row(controls=controls, spacing=8, expand=True)


def make_sticker_top_card(title: str, data: dict, users: dict, previews: dict[str, dict[int, Any]],
                          unit: str | None = None) -> ft.Container:
    """
    Создаёт карточку топа стикеров с предпросмотром и ссылкой на файл
    :param title: заголовок карточки
    :param data: статистика вида стикер -> пользователь -> количество
    :param users: словарь пользователей
    :param previews: словарь предпросмотров
    :param unit: единица измерения
    :return: контейнер Flet
    """
    rows = top_from_nested_counter(data, None)
    row_column = ft.Column(spacing=6)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for item, total, details in rows[:visible_count]:
            detail_text = user_details_text(details, users, 5)
            row_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    make_sticker_control(item, previews),
                                    ft.Text(format_value(total, unit or ''), size=16, weight=ft.FontWeight.BOLD),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(detail_text or 'Нет разбивки по пользователям', size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                    ),
                    padding=ft.Padding(left=4, top=8, right=4, bottom=8)
                )
            )

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=6),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_message_top_card(
        title: str,
        rows: list[tuple[Any, int]],
        previews: dict[str, dict[int, Any]],
        unit: str = 'симв.'
) -> ft.Container:
    """
    Создаёт карточку топа сообщений или файлов
    :param title: заголовок карточки
    :param rows: данные топа
    :param previews: словарь предпросмотров
    :param unit: единица измерения
    :return: контейнер Flet
    """
    row_column = ft.Column(spacing=8)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for index, (item, count) in enumerate(rows[:visible_count], start=1):
            row_column.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f'{index}.', width=32, color=ft.Colors.ON_SURFACE_VARIANT),
                        make_message_or_file_control(item, previews),
                        ft.Text(format_value(count, unit), weight=ft.FontWeight.BOLD),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=8),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_file_top_card(title: str, rows: list[tuple[Any, int]], previews: dict[str, dict[int, Any]],
                       unit: str) -> ft.Container:
    """
    Создаёт карточку топа файлов
    :param title: заголовок карточки
    :param rows: данные топа
    :param previews: словарь предпросмотров
    :param unit: единица измерения
    :return: контейнер Flet
    """
    row_column = ft.Column(spacing=8)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for index, (item, count) in enumerate(rows[:visible_count], start=1):
            row_column.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f'{index}.', width=32, color=ft.Colors.ON_SURFACE_VARIANT),
                        make_file_control(item, previews),
                        ft.Text(format_value(count, unit), weight=ft.FontWeight.BOLD),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=8),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_stat_card(title: str, value: str, subtitle: str | None = None) -> ft.Container:
    """
    Создаёт карточку общей статистики
    :param title: название статистики
    :param value: значение статистики
    :param subtitle: дополнительный текст
    :return: контейнер Flet
    """
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(title, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(value, size=28, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle or '', size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=4,
        ),
        padding=16,
        border_radius=16,
        bgcolor=RESULT_CARD_BG_3,
        expand=True,
    )


def make_user_row(user_id: str | None, count: int, users: dict, unit: str | None = None) -> ft.Container:
    """
    Создаёт строку пользователя для отображения в топе
    :param user_id: id пользователя
    :param count: значение статистики
    :param users: словарь пользователей
    :param unit: единица измерения
    :return: контейнер Flet
    """
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(user_name(user_id, users), size=15, weight=ft.FontWeight.W_600),
                        ft.Text(str(user_id), size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.Text(format_value(count, unit or ''), size=16, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=4, top=8, right=4, bottom=8)
    )


def make_podium_place(user_id: str | None, count: int, users: dict, place: int, height: int,
                      unit: str | None = None) -> ft.Container:
    """
    Создаёт одну ступень пьедестала для пользовательского топа
    :param user_id: id пользователя
    :param count: значение статистики
    :param users: словарь пользователей
    :param place: место в топе
    :param height: высота ступени
    :param unit: единица измерения
    :return: контейнер Flet
    """
    place_colors = {
        1: ACCENT,
        2: DISCORD,
        3: WARNING,
    }
    medal_icons = {
        1: ft.Icons.EMOJI_EVENTS,
        2: ft.Icons.MILITARY_TECH,
        3: ft.Icons.STAR,
    }

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(medal_icons.get(place, ft.Icons.PERSON), size=24, color=TEXT),
                    width=42,
                    height=42,
                    border_radius=21,
                    bgcolor=place_colors.get(place, CARD_BG_3),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(f'{place} место', size=12, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    user_name(user_id, users),
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    format_value(count, unit or ''),
                    size=17,
                    weight=ft.FontWeight.BOLD,
                    color=place_colors.get(place, TEXT),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.Text(f'#{place}', size=22, weight=ft.FontWeight.BOLD),
                    height=height,
                    border_radius=ft.BorderRadius(top_left=18, top_right=18, bottom_left=8, bottom_right=8),
                    bgcolor=RESULT_CARD_BG_3,
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.END,
            spacing=6,
        ),
        padding=ft.Padding(left=8, top=8, right=8, bottom=0),
        expand=True,
    )


def make_users_podium(rows: list[tuple[Any, int]], users: dict, unit: str | None = None) -> ft.Control:
    """
    Создаёт пьедестал из первых трёх пользователей
    :param rows: отсортированные строки пользовательского топа
    :param users: словарь пользователей
    :param unit: единица измерения
    :return: элемент интерфейса Flet
    """
    podium_order = [
        (2, 118),
        (1, 154),
        (3, 92),
    ]
    controls = []
    for place, height in podium_order:
        if len(rows) >= place:
            user_id, count = rows[place - 1]
            controls.append(make_podium_place(user_id, count, users, place, height, unit))
        else:
            controls.append(ft.Container(expand=True))

    return ft.Container(
        content=ft.Row(
            controls=controls,
            vertical_alignment=ft.CrossAxisAlignment.END,
            spacing=8,
        ),
        padding=ft.Padding(left=4, top=8, right=4, bottom=10),
        border_radius=18,
        bgcolor=RESULT_CARD_BG_2,
    )


def make_simple_top_card(title: str, rows: list[tuple[Any, int]], unit: str | None = None) -> ft.Container:
    """
    Создаёт карточку простого топа
    :param title: заголовок карточки
    :param rows: данные топа
    :param unit: единица измерения
    :return: контейнер Flet
    """
    row_column = ft.Column(spacing=8)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for index, (item, count) in enumerate(rows[:visible_count], start=1):
            row_column.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f'{index}.', width=32, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(str(item), expand=True, selectable=True),
                        ft.Text(format_value(count, unit or ''), weight=ft.FontWeight.BOLD),
                    ]
                )
            )

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=8),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_user_top_card(title: str, counter: Counter, users: dict, unit: str | None = None) -> ft.Container:
    """
    Создаёт карточку топа пользователей
    :param title: заголовок карточки
    :param counter: счётчик пользовательской статистики
    :param users: словарь пользователей
    :param unit: единица измерения
    :return: контейнер Flet
    """
    rows = counter_without_total(counter)
    row_column = ft.Column(spacing=4)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for user_id, count in rows[3:visible_count]:
            row_column.controls.append(make_user_row(user_id, count, users, unit))

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        controls.append(make_users_podium(rows, users, unit))
        if len(rows) > 3:
            controls.append(ft.Text('Остальные участники', size=14, color=TEXT_MUTED))
            render_rows(TOP_LIMIT)
            controls.append(row_column)
            controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=8),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


USER_STATS_LABELS = {
    'messages': ('Сообщения', 'сообщ.'),
    'reactions': ('Реакции', 'реакц.'),
    'photos': ('Фото', 'фото'),
    'videos': ('Видео', 'видео'),
    'stickers': ('Стикеры', 'стик.'),
    'files': ('Файлы', 'файл.'),
    'voice_messages': ('Голосовые', 'голос.'),
    'video_messages': ('Видеосообщения', 'видео-сообщ.'),
    'gifs': ('GIF', 'gif'),
    'audios': ('Аудио', 'аудио'),
    'smiles': ('Улыбочки', 'шт.'),
    'locations': ('Геолокации', 'гео'),
    'contacts': ('Контакты', 'конт.'),
    'polls': ('Опросы', 'опрос.'),
    'edited': ('Изменённые', 'сообщ.'),
    'forwarded': ('Пересланные', 'сообщ.'),
    'replies': ('Ответы', 'ответов'),
}


def make_user_stat_chip(label: str, value: Any, unit: str | None = None) -> ft.Container:
    """
    Создаёт небольшой показатель внутри карточки пользователя
    :param label: название показателя
    :param value: значение показателя
    :param unit: единица измерения
    :return: контейнер Flet
    """
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(label, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(format_value(value, unit or ''), size=15, weight=ft.FontWeight.BOLD),
            ],
            spacing=2,
        ),
        padding=10,
        border_radius=12,
        bgcolor=RESULT_CARD_BG_3,
        col={'xs': 6, 'md': 3, 'lg': 2},
    )


def make_user_stats_card(user_id: str | None, user_stats: dict, users: dict) -> ft.Container:
    """
    Создаёт карточку пользователя с несколькими статистиками
    :param user_id: id пользователя
    :param user_stats: статистика конкретного пользователя
    :param users: словарь пользователей
    :return: контейнер Flet
    """
    chips = []
    for stat_key, value in user_stats.items():
        label, unit = USER_STATS_LABELS.get(stat_key, (str(stat_key), None))
        chips.append(make_user_stat_chip(label, value, unit))

    if not chips:
        chips.append(
            ft.Container(
                content=ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT),
                col={'xs': 12},
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(user_name(user_id, users), size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(str(user_id), size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=2,
                ),
                ft.ResponsiveRow(controls=chips, spacing=8, run_spacing=8),
            ],
            spacing=12,
        ),
        padding=16,
        border_radius=16,
        bgcolor=RESULT_CARD_BG,
    )


def make_users_stats_section(data: dict, users: dict) -> ft.Container:
    """
    Создаёт отдельный блок карточек пользователей с поиском по имени и user_id
    :param data: статистика вида user_id -> stat -> count
    :param users: словарь пользователей
    :return: контейнер Flet
    """
    all_rows = sorted(
        data.items(),
        key=lambda item: item[1].get('messages', 0),
        reverse=True,
    )
    rows = list(all_rows)
    row_column = ft.Column(spacing=10)
    button_holder = ft.Column(spacing=0)
    search_field = ft.TextField(
        label='Поиск пользователя',
        hint_text='Введите имя или user_id',
        prefix_icon=ft.Icons.SEARCH,
        border_radius=14,
        bgcolor=CARD_BG_2,
        expand=True,
    )
    search_status = ft.Text('', size=12, color=TEXT_MUTED)

    def filter_rows(query: str) -> list[tuple[Any, dict]]:
        """
        Фильтрует карточки пользователей по имени и user_id
        :param query: поисковая строка
        :return: отфильтрованные строки
        """
        normalized_query = query.strip().lower()
        if not normalized_query:
            return list(all_rows)

        result = []
        for user_id, user_stats in all_rows:
            name = user_name(user_id, users).lower()
            user_id_text = str(user_id).lower()
            if normalized_query in name or normalized_query in user_id_text:
                result.append((user_id, user_stats))
        return result

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        if not rows:
            row_column.controls.append(ft.Text('Пользователь не найден', color=TEXT_MUTED))
            return

        for user_id, user_stats in rows[:visible_count]:
            row_column.controls.append(make_user_stats_card(user_id, user_stats, users))

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    def search_user(_: ft.ControlEvent) -> None:
        """
        Обновляет список карточек пользователей по поисковому запросу
        :param _: событие интерфейса
        :return: None
        """
        nonlocal rows
        rows = filter_rows(search_field.value or '')
        if search_field.value and rows:
            search_status.value = f'Найдено пользователей: {len(rows)}'
        else:
            search_status.value = ''
        render_rows(TOP_LIMIT)
        row_column.update()
        button_holder.update()
        search_status.update()

    search_field.on_change = search_user
    search_field.on_submit = search_user

    controls = [
        ft.Text('Карточки пользователей', size=24, weight=ft.FontWeight.BOLD),
        ft.Text(
            'Введите имя или user_id, чтобы найти конкретоного пользователя',
            size=13,
            color=TEXT_MUTED,
        ),
        search_field,
        search_status,
    ]

    if not all_rows:
        controls.append(ft.Text('Нет данных', color=TEXT_MUTED))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=12),
        padding=0,
    )


def make_nested_top_card(title: str, data: dict, users: dict, unit: str | None = None) -> ft.Container:
    """
    Создаёт карточку вложенного топа
    :param title: заголовок карточки
    :param data: статистика вида объект -> пользователь -> количество
    :param users: словарь пользователей
    :param unit: единица измерения
    :return: контейнер Flet
    """
    rows = top_from_nested_counter(data, None)
    row_column = ft.Column(spacing=6)
    button_holder = ft.Column(spacing=0)

    def render_rows(visible_count: int) -> None:
        row_column.controls.clear()
        button_holder.controls.clear()

        for item, total, details in rows[:visible_count]:
            detail_text = user_details_text(details, users, 5)
            row_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(str(item), size=16, weight=ft.FontWeight.W_600, expand=True,
                                            selectable=True),
                                    ft.Text(format_value(total, unit or ''), size=16, weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            ft.Text(detail_text or 'Нет разбивки по пользователям', size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                    ),
                    padding=ft.Padding(left=4, top=8, right=4, bottom=8)
                )
            )

        button = make_show_more_button(rows, visible_count, render_rows, button_holder)
        if button:
            button_holder.controls.append(button)

    controls = [ft.Text(title, size=20, weight=ft.FontWeight.BOLD)]

    if not rows:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        render_rows(TOP_LIMIT)
        controls.append(row_column)
        controls.append(button_holder)

    return ft.Container(
        content=ft.Column(controls=controls, spacing=6),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def normalize_locations(locations: list[tuple[Any, Any]]) -> list[tuple[str, float, float, datetime.datetime]]:
    """
    Отбрасывает некорректные координаты и приводит их к числам
    :param locations: список координат
    :return: список валидных координат
    """
    result = []
    for location in locations:
        if not isinstance(location, (list, tuple)) or len(location) < 2:
            continue

        try:
            latitude = float(location[1])
            longitude = float(location[2])
        except (TypeError, ValueError):
            continue

        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            result.append((location[0], latitude, longitude, location[3]))

    return result


def get_locations_center(locations: list[tuple[str, float, float, datetime.datetime]]) -> tuple[float, float]:
    """
    Возвращает центр карты по списку координат
    :param locations: список координат
    :return: широта и долгота центра
    """
    latitude = sum(location[1] for location in locations) / len(locations)
    longitude = sum(location[2] for location in locations) / len(locations)
    return latitude, longitude


def get_locations_zoom(locations: list[tuple[str, float, float, datetime.datetime]]) -> float:
    """
    Подбирает начальный масштаб карты, чтобы точки были видны
    :param locations: список координат
    :return: начальный масштаб карты
    """
    if len(locations) <= 1:
        return 13

    latitudes = [location[1] for location in locations]
    longitudes = [location[2] for location in locations]
    spread = max(
        max(latitudes) - min(latitudes),
        max(longitudes) - min(longitudes),
    )

    if spread > 120:
        return 1
    if spread > 60:
        return 2
    if spread > 25:
        return 3
    if spread > 10:
        return 4
    if spread > 5:
        return 5
    if spread > 2:
        return 6
    if spread > 1:
        return 7
    if spread > 0.5:
        return 8
    if spread > 0.1:
        return 10
    return 12


def make_locations_map(locations: list[tuple[str, float, float, datetime.datetime]], users: dict) -> ft.Control:
    """
    Создаёт интерактивную карту с точками геопозиций
    :param locations: список координат
    :param users: словарь пользователей
    :return: элемент интерфейса Flet
    """
    if ftm is None:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Карта недоступна', size=16, weight=ft.FontWeight.BOLD),
                    ft.Text('Установите зависимость: pip install flet-map'),
                ],
                spacing=6,
            ),
            padding=16,
            border_radius=14,
            bgcolor=RESULT_CARD_BG_3,
        )

    center_latitude, center_longitude = get_locations_center(locations)
    markers = [
        ftm.Marker(
            coordinates=ftm.MapLatitudeLongitude(latitude, longitude),
            width=30,
            height=30,
            content=ft.Icon(
                ft.Icons.LOCATION_ON,
                size=30,
                tooltip=f'{user_name(user_id, users)}\n{latitude:.6f}, {longitude:.6f}\n{date}',
                color='#000000',
            ),
        )
        for user_id, latitude, longitude, date in locations
    ]

    return ft.Container(
        content=ftm.Map(
            height=520,
            initial_center=ftm.MapLatitudeLongitude(center_latitude, center_longitude),
            initial_zoom=get_locations_zoom(locations),
            min_zoom=1,
            max_zoom=18,
            interaction_configuration=ftm.InteractionConfiguration(
                flags=ftm.InteractionFlag.ALL
            ),
            layers=[
                ftm.TileLayer(
                    url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    user_agent_package_name='tgstat/1.0',
                ),
                ftm.SimpleAttribution(text='OpenStreetMap contributors'),
                ftm.MarkerLayer(markers=markers),
            ],
        ),
        height=520,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def make_locations_card(locations: list[tuple[Any, Any]], users: dict) -> ft.Container:
    """
    Создаёт карточку с картой координат
    :param locations: список координат
    :param users: список пользователей
    :return: контейнер Flet
    """
    prepared_locations = normalize_locations(locations)
    controls = [ft.Text('Карта геопозиций', size=20, weight=ft.FontWeight.BOLD)]

    if not prepared_locations:
        controls.append(ft.Text('Нет данных', color=ft.Colors.ON_SURFACE_VARIANT))
    else:
        controls.extend([
            ft.Text(
                f'Найдено точек: {len(prepared_locations)}. Наведите на точку, чтобы узнать больше',
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            make_locations_map(prepared_locations, users),
        ])

    return ft.Container(
        content=ft.Column(controls=controls, spacing=12),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_word_search(stats: dict) -> ft.Container:
    """
    Создаёт блок поиска по словам
    :param stats: словарь статистик
    :return: контейнер Flet
    """
    words = stats['count_words_by_user']
    users = stats['users']
    result_column = ft.Column(spacing=6)
    button_holder = ft.Column(spacing=0)
    search_field = ft.TextField(
        label='Поиск слова',
        hint_text='Например: привет',
        expand=True,
    )
    matches = []

    def render_matches(visible_count: int) -> None:
        """
        Отображает найденные слова
        :param visible_count: количество видимых строк
        :return: None
        """
        result_column.controls.clear()
        button_holder.controls.clear()

        for word, total, details in matches[:visible_count]:
            detail_text = user_details_text(details, users)
            result_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(word, size=15, weight=ft.FontWeight.W_600, expand=True),
                                    ft.Text(format_value(total, 'слов'), weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            ft.Text(detail_text or 'Нет разбивки по пользователям', size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                    ),
                    padding=ft.Padding(left=4, top=8, right=4, bottom=8)
                )
            )

        button = make_show_more_button(matches, visible_count, render_matches, button_holder)
        if button:
            button_holder.controls.append(button)

    def search_word(_: ft.ControlEvent) -> None:
        """
        Выполняет поиск слова по собранной статистике
        :param _: событие интерфейса
        :return: None
        """
        query = chat_backend.clean_text(search_field.value or '').strip()
        result_column.controls.clear()
        button_holder.controls.clear()
        matches.clear()

        if not query:
            result_column.controls.append(ft.Text('Введите слово для поиска'))
        else:
            for word, counter in words.items():
                if query in word:
                    details = counter_without_total(counter)
                    matches.append((word, counter.get('total', 0), details))
            matches.sort(key=lambda row: row[1], reverse=True)

            if not matches:
                result_column.controls.append(ft.Text('Ничего не найдено'))
            else:
                render_matches(TOP_LIMIT)

        result_column.update()
        button_holder.update()

    search_field.on_submit = search_word

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text('Поиск по словам', size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        search_field,
                        ft.Button('Найти', on_click=search_word),
                    ]
                ),
                result_column,
                button_holder,
            ],
            spacing=10,
        ),
        padding=18,
        border_radius=18,
        bgcolor=RESULT_CARD_BG,
    )


def make_collapsible_section(title: str, controls: list[ft.Control]) -> ft.Container:
    """
    Создаёт секцию результатов, которая открывается по кнопке
    :param title: заголовок секции
    :param controls: элементы секции
    :return: контейнер Flet
    """
    content = ft.Column(controls=controls, spacing=14, visible=False)
    button = ft.Button(content=ft.Text('Открыть'))

    def toggle_section(event: ft.ControlEvent) -> None:
        content.visible = not content.visible
        button.content.value = 'Скрыть' if content.visible else 'Открыть'
        button.update()
        content.update()

    button.on_click = toggle_section

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(title, size=24, weight=ft.FontWeight.BOLD, expand=True),
                        button,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                content,
            ],
            spacing=12,
        ),
        padding=18,
        border_radius=18,
        bgcolor=CARD_BG_2,
    )


def make_section(title: str, controls: list[ft.Control]) -> ft.Container:
    """
    Создаёт секцию результатов
    :param title: заголовок секции
    :param controls: элементы секции
    :return: контейнер Flet
    """
    return ft.Container(
        content=ft.Column(
            controls=[ft.Text(title, size=24, weight=ft.FontWeight.BOLD), *controls],
            spacing=14,
        ),
        padding=0,
    )


def build_results_view(stats: dict) -> list[ft.Control]:
    """
    Формирует элементы страницы с результатами анализа
    :param stats: словарь статистик
    :return: список элементов интерфейса Flet
    """
    users = stats.get('users', {})
    previews = stats.get('_message_previews', {'texts': {}, 'files': {}, 'sticker_files': {}})
    selected_stats = set(stats.get('_selected_statistics', []))

    summary_cards = []
    if 'count_msgs_by_user' in selected_stats:
        total_messages = sum(stats.get('count_msgs_by_user', Counter()).values())
        summary_cards.append(
            ft.Container(make_stat_card('Сообщения', format_value(total_messages, 'сообщ.')), col={'xs': 12, 'md': 2})
        )
    if users:
        summary_cards.append(
            ft.Container(make_stat_card('Пользователи', format_value(len(users), 'чел.')), col={'xs': 12, 'md': 2})
        )
    if 'count_words_by_user' in selected_stats:
        total_words = sum(counter.get('total', 0) for counter in stats.get('count_words_by_user', {}).values())
        summary_cards.append(
            ft.Container(make_stat_card('Слова', format_value(total_words, 'слов')), col={'xs': 12, 'md': 2})
        )
    if 'max_file_size' in selected_stats:
        summary_cards.append(
            ft.Container(make_stat_card('Файлы', format_value(len(stats.get('max_file_size', [])), 'файл.')),
                         col={'xs': 12, 'md': 2})
        )
    if 'count_reactions_by_user' in selected_stats or 'count_total_reactions_by_user' in selected_stats:
        if 'count_reactions_by_user' in stats:
            total_reactions = sum(
                counter.get('total', 0) for counter in stats.get('count_reactions_by_user', {}).values())
        else:
            total_reactions = sum(stats.get('count_total_reactions_by_user', Counter()).values())
        summary_cards.append(
            ft.Container(make_stat_card('Реакции', format_value(total_reactions, 'реакций')), col={'xs': 12, 'md': 2})
        )
    if 'locations' in selected_stats:
        summary_cards.append(
            ft.Container(make_stat_card('Геоточки', format_value(len(stats.get('locations', [])), 'точек')),
                         col={'xs': 12, 'md': 2})
        )

    user_card_builders = [
        ('count_msgs_by_user',
         lambda: make_user_top_card('Топ пользователей по сообщениям', stats['count_msgs_by_user'], users, 'сообщ.')),
        ('count_total_reactions_by_user',
         lambda: make_user_top_card('Топ пользователей по реакциям', stats['count_total_reactions_by_user'], users,
                                    'реакц.')),
        ('count_photos_by_user',
         lambda: make_user_top_card('Топ пользователей по фото', stats['count_photos_by_user'], users, 'фото')),
        ('count_videos_by_user',
         lambda: make_user_top_card('Топ пользователей по видео', stats['count_videos_by_user'], users, 'видео')),
        ('count_stickers_by_user',
         lambda: make_user_top_card('Топ пользователей по стикерам', stats['count_stickers_by_user'], users, 'стик.')),
        ('count_files_by_user',
         lambda: make_user_top_card('Топ пользователей по файлам', stats['count_files_by_user'], users, 'файл.')),
        ('count_voice_msgs_by_user',
         lambda: make_user_top_card('Топ пользователей по голосовым сообщениям', stats['count_voice_msgs_by_user'],
                                    users, 'голос.')),
        ('count_video_msgs_by_user',
         lambda: make_user_top_card('Топ пользователей по видеосообщениям', stats['count_video_msgs_by_user'], users,
                                    'видео-сообщ.')),
        ('count_gifs_by_user',
         lambda: make_user_top_card('Топ пользователей по GIF', stats['count_gifs_by_user'], users, 'gif')),
        ('count_audios_by_user',
         lambda: make_user_top_card('Топ пользователей по аудио', stats['count_audios_by_user'], users, 'аудио')),
        ('count_smiles_by_user',
         lambda: make_user_top_card('Топ пользователей по улыбочкам)', stats['count_smiles_by_user'], users, 'шт.')),
        ('count_locations_by_user',
         lambda: make_user_top_card('Топ пользователей по геолокациям', stats['count_locations_by_user'], users,
                                    'гео')),
        ('count_contacts_by_user',
         lambda: make_user_top_card('Топ пользователей по контактам', stats['count_contacts_by_user'], users, 'конт.')),
        ('count_polls_by_user',
         lambda: make_user_top_card('Топ пользователей по опросам', stats['count_polls_by_user'], users, 'опрос.')),
        ('count_edited_by_user',
         lambda: make_user_top_card('Топ пользователей по изменению сообщений', stats['count_edited_by_user'], users,
                                    'сообщ.')),
        ('count_forwarded_by_user',
         lambda: make_user_top_card('Топ пользователей по пересылке сообщений', stats['count_forwarded_by_user'], users,
                                    'сообщ.')),
        ('count_replies_by_user',
         lambda: make_user_top_card('Топ пользователей по ответам', stats['count_replies_by_user'], users, 'ответов')),
    ]

    text_card_builders = [
        ('longest_msg',
         lambda: make_message_top_card('Самые длинные сообщения', stats['longest_msg'], previews, 'симв.')),
        ('count_words_by_user', lambda: make_nested_top_card('Топ слов', stats['count_words_by_user'], users, 'слов')),
        ('count_letters_by_user',
         lambda: make_nested_top_card('Топ букв', stats['count_letters_by_user'], users, 'букв')),
        (
            'count_digits_by_user', lambda: make_nested_top_card(
                'Топ цифр', stats['count_digits_by_user'], users, 'цифр')),
        ('count_emojis_by_user',
         lambda: make_nested_top_card('Топ эмодзи', stats['count_emojis_by_user'], users, 'эмодзи')),
        ('count_laugh',
         lambda: make_simple_top_card('Топ смеха', top_from_info_counter(stats['count_laugh'], None), 'раз')),
        ('count_text_types',
         lambda: make_simple_top_card('Типы текста', top_from_info_counter(stats['count_text_types'], None), 'фрагм.')),
        ('programming_languages_count', lambda: make_simple_top_card('Языки программирования в pre-блоках',
                                                                     top_from_info_counter(
                                                                         stats['programming_languages_count'], None),
                                                                     'блоков')),
        ('custom_phrases_count_by_user',
         lambda: make_nested_top_card('Кастомные фразы', stats['custom_phrases_count_by_user'], users, 'раз')),
        ('count_words_by_user', lambda: make_word_search(stats)),
    ]

    reaction_and_reply_builders = [
        ('count_reactions_by_user',
         lambda: make_nested_top_card('Реакции', stats['count_reactions_by_user'], users, 'реакций')),
        ('most_reacted',
         lambda: make_message_top_card('Самые залайканные сообщения', stats['most_reacted'], previews, 'реакций')),
        ('msgs_by_replies_count', lambda: make_message_top_card('Сообщения, на которые чаще всего отвечали',
                                                                top_from_info_counter(stats['msgs_by_replies_count'],
                                                                                      None), previews,
                                                                'ответов')),
    ]

    file_and_media_builders = [
        ('max_file_size', lambda: make_file_top_card('Самые большие файлы', stats['max_file_size'], previews, 'байт')),
        ('longest_voice_msg',
         lambda: make_file_top_card('Самые длинные голосовые сообщения', stats['longest_voice_msg'], previews, 'сек.')),
        ('longest_video_msg',
         lambda: make_file_top_card('Самые длинные видеосообщения', stats['longest_video_msg'], previews, 'сек.')),
        ('longest_video', lambda: make_file_top_card('Самые длинные видео', stats['longest_video'], previews, 'сек.')),
        ('longest_audio', lambda: make_file_top_card('Самые длинные аудио', stats['longest_audio'], previews, 'сек.')),
        ('longest_gif', lambda: make_file_top_card('Самые длинные GIF', stats['longest_gif'], previews, 'сек.')),
        ('count_stickers',
         lambda: make_sticker_top_card('Топ стикеров', stats['count_stickers'], users, previews, 'раз')),
    ]

    other_builders = [
        ('count_by_day',
         lambda: make_simple_top_card('Сообщения по дням', top_from_info_counter(stats['count_by_day'], None),
                                      'сообщ.')),
        ('service_action_dict',
         lambda: make_nested_top_card('Сервисные действия', stats['service_action_dict'], users, 'действий')),
        ('forwarded_from_count',
         lambda: make_simple_top_card('Откуда пересылали', top_from_info_counter(stats['forwarded_from_count'], None),
                                      'сообщ.')),
        ('count_via_by_user',
         lambda: make_nested_top_card('Сообщения через ботов', stats['count_via_by_user'], users, 'сообщ.')),
        ('locations', lambda: make_locations_card(stats['locations'], users)),
    ]

    def build_cards(builders: list[tuple[str, Any]]) -> list[ft.Control]:
        return [builder() for stat_key, builder in builders if stat_key in selected_stats and stat_key in stats]

    sections = []
    for title, builders in [
        ('Топы пользователей', user_card_builders),
        ('Текстовые статистики', text_card_builders),
        ('Реакции и ответы', reaction_and_reply_builders),
        ('Файлы и медиа', file_and_media_builders),
        ('Прочее', other_builders),
    ]:
        cards = build_cards(builders)
        if cards:
            sections.append(make_collapsible_section(title, cards))

    chat_name = stats.get('_chat_name', 'Без названия')
    chat_type = chat_type_label(stats.get('_chat_type'))
    controls = [
        ft.Text(f'Статистика {chat_type} \"{chat_name}\"', size=30, weight=ft.FontWeight.BOLD),
        ft.Text('Общая статистика и выбранные разделы анализа', size=15, color=TEXT_MUTED),
    ]
    if summary_cards:
        controls.append(ft.ResponsiveRow(controls=summary_cards, spacing=12, run_spacing=12))
    if 'users_stats' in selected_stats and 'users_stats' in stats:
        controls.append(make_users_stats_section(stats['users_stats'], users))
    controls.extend(sections)
    return controls


async def main(page: ft.Page) -> None:
    """
    Запускает пользовательский интерфейс приложения
    :param page: корневая страница Flet
    :return: None
    """
    page.title = 'TgStat'
    page.window.icon = platform_utils.get_app_icon_path()
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = APP_BG
    page.window.min_width = 900
    page.window.min_height = 700
    page.theme = ft.Theme(
        color_scheme_seed=ACCENT,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    selected_path = ft.Text('Папка не выбрана', color=TEXT_MUTED, selectable=True)
    custom_phrases_field = ft.TextField(
        label='Кастомные фразы',
        hint_text='Каждая фраза с новой строки',
        multiline=True,
        min_lines=4,
        max_lines=7,
        border_radius=14,
        bgcolor=CARD_BG_2,
    )
    custom_phrases_block = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text('Дополнительный поиск по кастомным фразам', size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    'Необязательная функция: укажите фразы, которые нужно отдельно посчитать в сообщениях. '
                    'Каждая фраза вводится с новой строки',
                    size=13,
                    color=TEXT_MUTED,
                ),
                custom_phrases_field,
            ],
            spacing=8,
        ),
        visible=False,
    )
    status_text = ft.Text('Выберите папку экспорта Telegram Desktop', color=TEXT_MUTED)
    analyze_button = make_primary_button('Начать анализ', disabled=True)

    analyze_button.style = ft.ButtonStyle(
        bgcolor={
            ft.ControlState.DEFAULT: ACCENT,
            ft.ControlState.DISABLED: '#2A2E38',
        },
        color={
            ft.ControlState.DEFAULT: ft.Colors.WHITE,
            ft.ControlState.DISABLED: '#7A7F8A',
        },
    )

    stat_checkboxes = {}
    group_checkboxes = {}
    all_statistics_checkbox = ft.Checkbox(label='Все статистики', value=True)

    def set_screen(control: ft.Control) -> None:
        """
        Заменяет текущий экран приложения
        :param control: новый экран
        :return: None
        """
        page.controls.clear()
        page.add(make_page_shell(control))
        page.update()

    async def show_top_notification(message: str, duration: float = 2, bgcolor: str = SUCCESS) -> None:
        notification = ft.Container(
            content=ft.Text(message, color=TEXT, size=14, weight=ft.FontWeight.W_600),
            padding=ft.Padding(left=18, top=12, right=18, bottom=12),
            border_radius=14,
            bgcolor=bgcolor,
            opacity=0,
            offset=ft.Offset(0, -0.25),
            animate_opacity=250,
            animate_offset=250,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color='#55000000',
                offset=ft.Offset(0, 6),
            ),
        )

        wrapper = ft.Container(
            content=notification,
            alignment=ft.Alignment(0, -1),
            padding=ft.Padding(left=0, top=24, right=0, bottom=0),
            expand=True,
        )

        page.overlay.append(wrapper)
        page.update()

        await asyncio.sleep(0.5)

        notification.opacity = 1
        notification.offset = ft.Offset(0, 0)
        page.update()

        await asyncio.sleep(duration)

        notification.opacity = 0
        notification.offset = ft.Offset(0, -0.25)
        page.update()

        await asyncio.sleep(0.25)

        if wrapper in page.overlay:
            page.overlay.remove(wrapper)
            page.update()

    def selected_statistics() -> list[str]:
        """
        Возвращает выбранные пользователем статистики
        :return: список ключей статистик
        """
        return [key for key, checkbox in stat_checkboxes.items() if checkbox.value]

    def sync_parent_checkboxes() -> None:
        """
        Синхронизирует состояние родительских чекбоксов
        :return: None
        """
        for group_key, _, items in STAT_GROUPS:
            group_checkboxes[group_key].value = all(stat_checkboxes[stat_key].value for stat_key, _ in items)
        all_statistics_checkbox.value = all(checkbox.value for checkbox in stat_checkboxes.values())

    def on_all_statistics_change(event: ft.ControlEvent) -> None:
        """
        Выбирает или снимает все статистики
        :param event: событие интерфейса
        :return: None
        """
        value = bool(event.control.value)
        for checkbox in stat_checkboxes.values():
            checkbox.value = value
        for checkbox in group_checkboxes.values():
            checkbox.value = value
        page.update()

    def make_group_change_handler(group_key: str) -> Any:
        """
        Создаёт обработчик выбора группы статистик
        :param group_key: ключ группы
        :return: обработчик события
        """

        def on_group_change(event: ft.ControlEvent) -> None:
            value = bool(event.control.value)
            items = next(items for key, _, items in STAT_GROUPS if key == group_key)
            for stat_key, _ in items:
                stat_checkboxes[stat_key].value = value
            sync_parent_checkboxes()
            page.update()

        return on_group_change

    def on_stat_change(_: ft.ControlEvent) -> None:
        """
        Обновляет родительские чекбоксы после выбора отдельной статистики
        :param _: событие интерфейса
        :return: None
        """
        sync_parent_checkboxes()
        page.update()

    statistics_selector_controls = [all_statistics_checkbox]
    all_statistics_checkbox.on_change = on_all_statistics_change

    for group_key, group_title, items in STAT_GROUPS:
        group_checkbox = ft.Checkbox(label=group_title, value=True)
        group_checkbox.on_change = make_group_change_handler(group_key)
        group_checkboxes[group_key] = group_checkbox

        children = []
        for stat_key, label in items:
            checkbox = stat_checkboxes.get(stat_key)
            if checkbox is None:
                checkbox = ft.Checkbox(label=label, value=True, on_change=on_stat_change)
                stat_checkboxes[stat_key] = checkbox

            children.append(
                ft.Container(
                    content=checkbox,
                    col={'xs': 12, 'md': 6},
                    padding=ft.Padding(left=28, top=0, right=0, bottom=0),
                )
            )

        statistics_selector_controls.append(group_checkbox)
        statistics_selector_controls.append(
            ft.ResponsiveRow(
                controls=children,
                spacing=0,
                run_spacing=0,
            )
        )

    statistics_selector = make_card(
        ft.Column(
            controls=[
                ft.Text('Выберите статистики', size=22, weight=ft.FontWeight.BOLD),
                ft.Text(
                    'Backend соберёт только выбранные статистики. Разделы результатов будут открываться по кнопке.',
                    size=13,
                    color=TEXT_MUTED,
                ),
                *statistics_selector_controls,
            ],
            spacing=2,
        ),
        padding=18,
        bgcolor=CARD_BG_2,
    )
    statistics_selector.visible = False

    def show_about_dialog(_: ft.ControlEvent) -> None:
        """
        Показывает всплывающее окно About
        :param _: событие интерфейса
        :return: None
        """

        async def open_about_url(_: ft.ControlEvent) -> None:
            await ft.UrlLauncher().launch_url(ABOUT_URL)

        about_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('О TgStat'),
            content=ft.Column(
                controls=[
                    ft.Text('TgStat — приложение для анализа чатов, каналов и групп Telegram'),
                    ft.Text(
                        spans=[
                            ft.TextSpan(
                                text='Подробнее о приложении можно узнать ',
                            ),
                            ft.TextSpan(
                                text='тут',
                                style=ft.TextStyle(
                                    color=LINK_COLOR,
                                    weight=ft.FontWeight.BOLD,
                                    decoration=ft.TextDecoration.UNDERLINE,
                                ),
                                on_click=open_about_url,
                            ),
                        ],
                    ),
                ],
                spacing=12,
                tight=True,
            ),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        about_dialog.actions = [
            ft.Button('Закрыть', on_click=lambda event: close_dialog())
        ]

        if about_dialog not in page.overlay:
            page.overlay.append(about_dialog)

        about_dialog.open = True
        page.update()

        def close_dialog() -> None:
            """
            Закрывает активное диалоговое окно
            :return: None
            """
            about_dialog.open = False
            page.update()

    def choose_folder(_: ft.ControlEvent) -> None:
        """
        Открывает окно выбора папки экспорта Telegram
        :param _: событие интерфейса
        :return: None
        """
        path = platform_utils.choose_directory('Выберите папку экспорта Telegram')
        if not path:
            return

        selected_path.value = path
        result_path = Path(path) / 'result.json'

        if result_path.exists():
            analyze_button.disabled = False
            custom_phrases_block.visible = True
            statistics_selector.visible = True
            status_text.value = 'Папка выбрана. Можно запускать анализ.'
            status_text.color = SUCCESS
        else:
            analyze_button.disabled = True
            custom_phrases_block.visible = False
            statistics_selector.visible = False
            status_text.value = 'В выбранной папке не найден result.json'
            status_text.color = WARNING

        page.update()

    async def open_saved_statistics(_: ft.ControlEvent) -> None:
        """
        Открывает ранее сохранённый JSON со статистикой
        :param _: событие интерфейса
        :return: None
        """
        path = platform_utils.choose_json_file('Выберите сохранённый JSON TgStat', get_saved_analyzes_folder())
        if not path:
            return

        try:
            stats = read_analysis_from_json(path)
            stats['_is_saved_analysis'] = True
        except Exception as error:
            status_text.value = f'Ошибка открытия статистики: {error}'
            status_text.color = WARNING
            show_start_screen()
            return

        show_results_screen(stats)

    def show_loading_screen(title: str = 'Идёт анализ чата...') -> None:
        """
        Показывает экран загрузки
        :param title: текст загрузки
        :return: None
        """
        set_screen(
            ft.Column(
                controls=[
                    ft.Container(height=80),
                    ft.Text('TgStat', size=42, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(title, size=18, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=12),
                    ft.ProgressRing(width=54, height=54, stroke_width=5, color=ACCENT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
            )
        )

    def show_results_screen(stats: dict) -> None:
        """
        Показывает страницу результатов анализа
        :param stats: словарь статистик
        :return: None
        """

        def save_results(_: ft.ControlEvent) -> None:
            """
            Запрашивает название анализа и сохраняет статистику в папку saved_analyzes
            :param _: событие интерфейса
            :return: None
            """
            name_field = ft.TextField(
                label='Название анализа',
                hint_text='Например: Семейный чат июнь 2026',
                autofocus=True,
                border_radius=14,
            )

            save_button = ft.Button('Сохранить', disabled=True)

            def close_dialog() -> None:
                save_dialog.open = False
                page.update()

            def update_save_button(_: ft.ControlEvent | None = None) -> None:
                has_name = bool((name_field.value or '').strip())
                save_button.disabled = not has_name
                name_field.error_text = None if has_name else name_field.error_text
                save_button.update()
                name_field.update()

            async def confirm_save(event: ft.ControlEvent | None = None) -> None:
                analysis_name = (name_field.value or '').strip()
                if not analysis_name:
                    name_field.error_text = 'Введите название анализа'
                    name_field.update()
                    return

                try:
                    stats['_analysis_name'] = analysis_name
                    output_path = save_analysis_to_json(stats, str(get_saved_analyzes_folder()))
                    close_dialog()
                    await show_top_notification(f'Статистика сохранена: {output_path.name}', bgcolor=SUCCESS)
                except Exception as error:
                    await show_top_notification(f'Ошибка сохранения: {error}', bgcolor=WARNING)

            name_field.on_change = update_save_button
            name_field.on_submit = confirm_save
            save_button.on_click = confirm_save

            save_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text('Сохранить анализ'),
                content=ft.Column(
                    controls=[
                        ft.Text(f'Файл будет сохранён в папку: {get_saved_analyzes_folder()}'),
                        ft.Text(
                            f'Важно: сохранятся только данные анализа. Данные чата, такие как фото, медиа и др.\n'
                            f'при повторном просмотре приложение будет искать в папке'
                        ),
                        ft.Text(f'{selected_path.value}'),
                        ft.Container(
                            content=name_field,
                            margin=ft.Margin(top=16, left=0, right=0, bottom=0),
                        )
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.Button('Отмена', on_click=lambda event: close_dialog()),
                    save_button,
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            if save_dialog not in page.overlay:
                page.overlay.append(save_dialog)
            save_dialog.open = True
            page.update()

        result_controls = build_results_view(stats)
        bottom_controls = []

        if not stats.get('_is_saved_analysis', False):
            bottom_controls.append(
                ft.Row(
                    controls=[make_primary_button('Сохранить', on_click=save_results)],
                    alignment=ft.MainAxisAlignment.END,
                )
            )
        set_screen(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text('TgStat', size=18, weight=ft.FontWeight.BOLD, color=ACCENT),
                                    ft.Text('Результаты анализа Telegram-экспорта', size=13, color=TEXT_MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            make_secondary_button('На главную', on_click=lambda event: show_start_screen()),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    *result_controls,
                    *bottom_controls,
                ],
                spacing=18,
            )
        )

    async def analyze(_: ft.ControlEvent) -> None:
        """
        Запускает анализ выбранного чата
        :param _: событие интерфейса
        :return: None
        """
        chat_path = selected_path.value
        phrases = parse_custom_phrases(custom_phrases_field.value or '')
        selected_stats = selected_statistics()

        if not selected_stats:
            status_text.value = 'Выберите хотя бы одну статистику'
            status_text.color = WARNING
            page.update()
            return

        show_loading_screen()

        try:
            stats = await asyncio.to_thread(chat_backend.main, chat_path, phrases, selected_stats)
            meta = await asyncio.to_thread(read_chat_meta, chat_path)
            stats['_chat_name'] = meta['name']
            stats['_chat_type'] = meta['type']
            stats['_is_saved_analysis'] = False
            stats['_selected_statistics'] = selected_stats
            if set(selected_stats) & PREVIEW_STAT_KEYS:
                stats['_message_previews'] = await asyncio.to_thread(collect_message_previews, chat_path)
            else:
                stats['_message_previews'] = {'texts': {}, 'files': {}, 'sticker_files': {}}
        except Exception as error:
            status_text.value = f'Ошибка анализа: {error}'
            status_text.color = WARNING
            show_start_screen()
            return

        show_results_screen(stats)

    analyze_button.on_click = analyze

    def reset_start_screen_state() -> None:
        """
        Возвращает главный экран в исходное состояние
        :return: None
        """
        selected_path.value = 'Папка не выбрана'
        selected_path.color = TEXT_MUTED
        status_text.value = 'Выберите папку экспорта Telegram Desktop'
        status_text.color = TEXT_MUTED
        analyze_button.disabled = True
        custom_phrases_field.value = ''
        custom_phrases_block.visible = False
        statistics_selector.visible = False
        all_statistics_checkbox.value = True
        for checkbox in stat_checkboxes.values():
            checkbox.value = True
        for checkbox in group_checkboxes.values():
            checkbox.value = True

    def show_start_screen() -> None:
        """
        Показывает начальный экран приложения
        :return: None
        """
        reset_start_screen_state()
        set_screen(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(expand=True),
                            make_secondary_button('About', on_click=show_about_dialog),
                        ],
                    ),
                    ft.Container(height=18),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=520,
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Image(
                                                        src=platform_utils.resource_path('assets/logo.png'),
                                                        width=56,
                                                        height=56,
                                                    ),
                                                    padding=ft.Padding(left=0, top=10, right=0, bottom=0)),
                                                ft.Text(
                                                    'TgStat',
                                                    size=52,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                            ],
                                            spacing=12,
                                        ),
                                        ft.Text(
                                            'Анализ чатов, каналов и групп Telegram',
                                            size=18,
                                            color=TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=8,
                                    horizontal_alignment=ft.CrossAxisAlignment.START,
                                ),
                            ),
                        ],
                    ),
                    ft.Container(height=14),
                    make_card(
                        ft.Column(
                            controls=[
                                ft.Text('Выберите источник данных', size=22, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    'Сначала выберите папку экспорта Telegram Desktop с файлом result.json. '
                                    'После этого появится выбор статистик',
                                    color=TEXT_MUTED,
                                ),
                                ft.Row(
                                    controls=[
                                        make_primary_button('Выбрать папку', on_click=choose_folder),
                                        make_secondary_button('Открыть сохранённую статистику',
                                                              on_click=open_saved_statistics),
                                    ],
                                    wrap=True,
                                    spacing=12,
                                ),
                                selected_path,
                                status_text,
                                custom_phrases_block,
                                statistics_selector,
                                ft.Row(
                                    controls=[analyze_button],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=16,
                        ),
                        padding=24,
                    ),
                ],
                spacing=16,
            )
        )

    show_start_screen()


platform_utils.configure_flet_view_path()
ft.run(main)
