import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import unicodedata
import regex

users = {}  # user_id -> name

# stats
service_action_dict = defaultdict(Counter)  # action -> user_id -> count
count_reactions_by_user = defaultdict(Counter)  # reaction -> user_id -> count
users_stats = defaultdict(dict)  # user_id -> stat -> count
most_reacted = []  # msg_id, count
count_by_day = Counter()  # day -> count
count_msgs_by_user = Counter()  # user_id -> count
count_total_reactions_by_user = Counter()
count_photos_by_user = Counter()
count_videos_by_user = Counter()
count_stickers_by_user = Counter()
count_files_by_user = Counter()
count_voice_msgs_by_user = Counter()
count_video_msgs_by_user = Counter()
count_gifs_by_user = Counter()
count_audios_by_user = Counter()
count_smiles_by_user = Counter()
count_locations_by_user = Counter()
count_contacts_by_user = Counter()
count_polls_by_user = Counter()
count_edited_by_user = Counter()
count_forwarded_by_user = Counter()
forwarded_from_count = Counter()
count_replies_by_user = Counter()
msgs_by_replies_count = Counter()
count_stickers = defaultdict(Counter)  # file_id -> user_id -> count
max_file_size = []  # file_id, size
longest_voice_msg = []  # file_id, length
longest_video_msg = []
longest_video = []
longest_audio = []
longest_gif = []
locations = []  # (user_id, lat, lon, day)
count_text_types = Counter()  # type -> count
count_words_by_user = defaultdict(Counter)  # word -> user_id -> count
count_letters_by_user = defaultdict(Counter)  # letter -> user_id -> count
count_digits_by_user = defaultdict(Counter)  # digit -> user_id -> count
count_emojis_by_user = defaultdict(Counter)  # emoji -> user_id -> count
count_laugh = Counter()  # laugh -> count
longest_msg = []  # msg_id, length
count_via_by_user = defaultdict(Counter)  # bot -> user_id -> count
programming_languages_count = Counter()  # language -> count
custom_phrases_count_by_user = defaultdict(Counter)  # phrase -> user_id -> count
cleaned_custom_phrases = []

EMOJI_PARTS = {'\ufe0f', '\u200d'}
EMOJI_PATTERN = regex.compile(
    r'(\p{Emoji_Presentation}|\p{Extended_Pictographic})')

TEXT_TYPES_FOR_WORDS = ('plain', 'italic', 'bold',
                        'underline', 'strikethrough',
                        'spoiler', 'blockquote', 'hashtag')
RU_LAUGH = set('хапыиэеоз')
EN_LAUGH_1 = set('hyaeon')
EN_LAUGH_2 = set('xd')

STAT_KEYS = {
    'service_action_dict',
    'count_reactions_by_user',
    'count_total_reactions_by_user',
    'most_reacted',
    'count_by_day',
    'count_msgs_by_user',
    'count_photos_by_user',
    'count_videos_by_user',
    'count_stickers_by_user',
    'count_files_by_user',
    'count_voice_msgs_by_user',
    'count_video_msgs_by_user',
    'count_gifs_by_user',
    'count_audios_by_user',
    'count_smiles_by_user',
    'count_locations_by_user',
    'count_contacts_by_user',
    'count_polls_by_user',
    'count_edited_by_user',
    'count_forwarded_by_user',
    'forwarded_from_count',
    'count_replies_by_user',
    'msgs_by_replies_count',
    'count_stickers',
    'max_file_size',
    'longest_voice_msg',
    'longest_video_msg',
    'longest_video',
    'longest_audio',
    'longest_gif',
    'locations',
    'count_text_types',
    'users_stats',
    'count_words_by_user',
    'count_letters_by_user',
    'count_digits_by_user',
    'count_emojis_by_user',
    'count_laugh',
    'longest_msg',
    'count_via_by_user',
    'programming_languages_count',
    'custom_phrases_count_by_user',
}

TEXT_STAT_KEYS = {
    'count_words_by_user',
    'count_letters_by_user',
    'count_digits_by_user',
    'count_emojis_by_user',
    'count_laugh',
    'count_text_types',
    'programming_languages_count',
    'custom_phrases_count_by_user',
    'longest_msg',
    'count_smiles_by_user',
}

SORTABLE_LIST_STATS = {
    'most_reacted': most_reacted,
    'max_file_size': max_file_size,
    'longest_voice_msg': longest_voice_msg,
    'longest_video_msg': longest_video_msg,
    'longest_video': longest_video,
    'longest_audio': longest_audio,
    'longest_gif': longest_gif,
    'longest_msg': longest_msg,
}

USER_STATS = {

}


def normalize_selected_stats(selected_stats: list[str] | set[str] | None) -> set[str]:
    """
    Приводит список выбранных статистик к множеству допустимых ключей
    :param selected_stats: выбранные статистики
    :return: множество ключей статистик
    """
    if selected_stats is None:
        return set(STAT_KEYS)
    return {stat for stat in selected_stats if stat in STAT_KEYS}


def need_stat(selected_stats: set[str], stat_key: str) -> bool:
    """
    Проверяет, нужно ли собирать статистику
    :param selected_stats: выбранные статистики
    :param stat_key: ключ статистики
    :return: True, если статистика нужна
    """
    return stat_key in selected_stats


def reset_stats() -> None:
    """
    Очищает все статистики перед новым анализом
    :return: None
    """
    users.clear()
    service_action_dict.clear()
    count_reactions_by_user.clear()
    most_reacted.clear()
    count_by_day.clear()
    count_msgs_by_user.clear()
    count_photos_by_user.clear()
    count_videos_by_user.clear()
    count_stickers_by_user.clear()
    count_files_by_user.clear()
    count_voice_msgs_by_user.clear()
    count_video_msgs_by_user.clear()
    count_gifs_by_user.clear()
    count_audios_by_user.clear()
    count_smiles_by_user.clear()
    count_locations_by_user.clear()
    count_contacts_by_user.clear()
    count_polls_by_user.clear()
    count_edited_by_user.clear()
    count_forwarded_by_user.clear()
    forwarded_from_count.clear()
    count_replies_by_user.clear()
    msgs_by_replies_count.clear()
    count_stickers.clear()
    max_file_size.clear()
    longest_voice_msg.clear()
    longest_video_msg.clear()
    longest_video.clear()
    longest_audio.clear()
    longest_gif.clear()
    locations.clear()
    count_text_types.clear()
    count_words_by_user.clear()
    count_letters_by_user.clear()
    count_digits_by_user.clear()
    count_emojis_by_user.clear()
    count_laugh.clear()
    longest_msg.clear()
    count_via_by_user.clear()
    programming_languages_count.clear()
    custom_phrases_count_by_user.clear()
    cleaned_custom_phrases.clear()
    users_stats.clear()
    count_total_reactions_by_user.clear()


def get_stats(selected_stats: set[str] | None = None) -> dict:
    """
    Возвращает все собранные статистики
    :return: словарь со статистиками
    """
    selected_stats = normalize_selected_stats(selected_stats)
    stats = {
        'users': users,
        'service_action_dict': service_action_dict,
        'count_reactions_by_user': count_reactions_by_user,
        'most_reacted': most_reacted,
        'count_by_day': count_by_day,
        'count_msgs_by_user': count_msgs_by_user,
        'count_photos_by_user': count_photos_by_user,
        'count_videos_by_user': count_videos_by_user,
        'count_stickers_by_user': count_stickers_by_user,
        'count_files_by_user': count_files_by_user,
        'count_voice_msgs_by_user': count_voice_msgs_by_user,
        'count_video_msgs_by_user': count_video_msgs_by_user,
        'count_gifs_by_user': count_gifs_by_user,
        'count_audios_by_user': count_audios_by_user,
        'count_smiles_by_user': count_smiles_by_user,
        'count_locations_by_user': count_locations_by_user,
        'count_contacts_by_user': count_contacts_by_user,
        'count_polls_by_user': count_polls_by_user,
        'count_edited_by_user': count_edited_by_user,
        'count_forwarded_by_user': count_forwarded_by_user,
        'forwarded_from_count': forwarded_from_count,
        'count_replies_by_user': count_replies_by_user,
        'msgs_by_replies_count': msgs_by_replies_count,
        'count_stickers': count_stickers,
        'max_file_size': max_file_size,
        'longest_voice_msg': longest_voice_msg,
        'longest_video_msg': longest_video_msg,
        'longest_video': longest_video,
        'longest_audio': longest_audio,
        'longest_gif': longest_gif,
        'locations': locations,
        'count_text_types': count_text_types,
        'count_words_by_user': count_words_by_user,
        'count_letters_by_user': count_letters_by_user,
        'count_digits_by_user': count_digits_by_user,
        'count_emojis_by_user': count_emojis_by_user,
        'count_laugh': count_laugh,
        'longest_msg': longest_msg,
        'count_via_by_user': count_via_by_user,
        'programming_languages_count': programming_languages_count,
        'custom_phrases_count_by_user': custom_phrases_count_by_user,
        'users_stats': users_stats,
        'count_total_reactions_by_user': count_total_reactions_by_user
    }
    return {
        key: value
        for key, value in stats.items()
        if key == 'users' or key in selected_stats
    }


def count_custom_phrases(text: str, user: str | None) -> None:
    """
    Считает кастомные фразы в тексте сообщения
    :param text: очищенный текст сообщения
    :param user: id автора сообщения
    :return: None
    """
    normalized_text = ' '.join(text.split())
    if not normalized_text:
        return

    normalized_text = f' {normalized_text} '
    for phrase in cleaned_custom_phrases:
        pattern = rf'(?<!\S){regex.escape(phrase)}(?!\S)'
        count = len(regex.findall(pattern, normalized_text))
        if count:
            custom_phrases_count_by_user[phrase]['total'] += count
            custom_phrases_count_by_user[phrase][user] += count


def clean_text(s: str) -> str:
    """
    Обрабатывает строку
    Оставляет только буквы, цифры и эмодзи и приводит к нижнему регистру
    :param s: строка
    :return: обработанная строка
    """
    return ''.join(
        c.lower()
        for c in s
        if c.isalnum()
        or c.isspace()
        or unicodedata.category(c).startswith('S')
        or c in EMOJI_PARTS
    )


def is_laugh(word: str) -> bool:
    """
    Проверяет, является ли слово смехом
    :param word: слово
    :return: True, если слово является смехом
    """
    letters = set(word)
    return (
            ((letters <= RU_LAUGH) and ('х' in letters) and (
                    len(word) > 2 or (len(word) > 1 and word[0] == 'х'))) or (
                    (letters <= EN_LAUGH_1) and ('h' in letters) and (
                    len(word) > 1)) or (
                    (letters <= EN_LAUGH_2) and (len(word) > 1))) and (
            word not in ['пох', 'пах', 'эхо', 'ах', 'эх', 'ох', 'пых', 'oh', 'ah', 'eh', 'he', 'hey']) and (
            set('хз') != letters) and not (
            re.fullmatch(r'запах(?:а|у|ом|е|и|ов|ам|ами|ах)?', word) or
            re.fullmatch(r'эпох(?:а|и|е|у|ой|ою|ами|ах)?', word)
    )


def is_emoji(symbol: str) -> bool:
    """
    Проверяет, является ли символ или графема эмодзи
    :param symbol: символ или графема
    :return: True, если это эмодзи
    """
    return bool(EMOJI_PATTERN.search(symbol))


def parse_service_msg(msg: dict) -> None:
    """
    Парсит сервисное сообщение по действию и исполнителю
    :param msg: сервисное сообщение в формате json
    :return: None
    """
    global service_action_dict
    action = msg.get('action')
    actor_id = msg.get('actor_id')
    service_action_dict[action]['total'] += 1
    service_action_dict[action][actor_id] += 1


def parse_file(msg: dict, selected_stats: set[str]) -> None:
    """
    Парсит сообщение с файлом по автору и размеру
    :param selected_stats: выбранные статистики
    :param msg: сообщение с файлом в формате json
    :return: None
    """
    file_id = msg.get('id')
    size = msg.get('file_size', 0)
    if need_stat(selected_stats, 'max_file_size'):
        max_file_size.append((file_id, size))

    if not msg.get('media_type') and need_stat(selected_stats, 'count_files_by_user'):
        count_files_by_user[msg.get('from_id')] += 1


def parse_photo(msg: dict, selected_stats: set[str]) -> None:
    """
    Парсит сообщение с фото по автору и размеру
    :param selected_stats: выбранные статистики
    :param msg: сообщение c фото в формате json
    :return: None
    """
    parse_file(msg, selected_stats)

    if need_stat(selected_stats, 'count_photos_by_user'):
        count_photos_by_user[msg.get('from_id')] += 1


def parse_media(msg: dict, selected_stats: set[str]) -> None:
    """
    Парсит медиа-сообщение по автору, длине, размеру и типу
    :param selected_stats: выбранные статистики
    :param msg: сообщение с медиа в формате json
    :return: None
    """
    parse_file(msg, selected_stats)

    file_id = msg.get('id')
    user = msg.get('from_id')
    media_type = msg.get('media_type')
    length = msg.get('duration_seconds', 0) or 0

    media_counters = {
        'video_file': count_videos_by_user,
        'animation': count_gifs_by_user,
        'sticker': count_stickers_by_user,
        'audio_file': count_audios_by_user,
        'voice_message': count_voice_msgs_by_user,
        'video_message': count_video_msgs_by_user,
    }

    media_stat_keys = {
        'video_file': 'count_videos_by_user',
        'animation': 'count_gifs_by_user',
        'sticker': 'count_stickers_by_user',
        'audio_file': 'count_audios_by_user',
        'voice_message': 'count_voice_msgs_by_user',
        'video_message': 'count_video_msgs_by_user',
    }

    if media_type in media_counters and need_stat(selected_stats, media_stat_keys[media_type]):
        media_counters[media_type][user] += 1

    if media_type == 'video_file' and need_stat(selected_stats, 'longest_video'):
        longest_video.append((file_id, length))
    elif media_type == 'animation' and need_stat(selected_stats, 'longest_gif'):
        longest_gif.append((file_id, length))
    elif media_type == 'audio_file' and need_stat(selected_stats, 'longest_audio'):
        longest_audio.append((file_id, length))
    elif media_type == 'voice_message' and need_stat(selected_stats, 'longest_voice_msg'):
        longest_voice_msg.append((file_id, length))
    elif media_type == 'video_message' and need_stat(selected_stats, 'longest_video_msg'):
        longest_video_msg.append((file_id, length))

    if media_type == 'sticker' and need_stat(selected_stats, 'count_stickers'):
        sticker = msg.get('file')
        count_stickers[sticker]['total'] += 1
        count_stickers[sticker][user] += 1


def parse_reactions(msg: dict, selected_stats: set[str]) -> None:
    """
    Парсит сообщение по реакциям
    :param selected_stats: выбранные статистики
    :param msg: сообщение в формате json
    :return: None
    """
    collect_reactions = need_stat(selected_stats, 'count_reactions_by_user')
    collect_most_reacted = need_stat(selected_stats, 'most_reacted')
    collect_total_reactions = need_stat(selected_stats, 'count_total_reactions_by_user')
    total_count = 0
    for reaction in msg.get('reactions', []):
        count = reaction.get('count', 0)
        reaction_type = reaction.get('type')
        if reaction_type == 'paid':
            emoji = 'paid'
        elif reaction_type == 'emoji':
            emoji = reaction.get('emoji')
        else:
            emoji = reaction.get('document_id')
        if collect_reactions:
            count_reactions_by_user[emoji]['total'] += count
        if collect_reactions or collect_total_reactions:
            for user in reaction.get('recent', []):
                user_id = user.get('from_id')
                if collect_reactions:
                    count_reactions_by_user[emoji][user_id] += 1
                if collect_total_reactions:
                    count_total_reactions_by_user[user_id] += 1
        if collect_most_reacted:
            total_count += count
    if collect_most_reacted:
        most_reacted.append((msg.get('id'), total_count))


def parse_text(msg: dict, selected_stats: set[str]) -> None:
    """
    Парсит текст сообщения по выбранным характеристикам
    :param msg: сообщение в формате json
    :param selected_stats: выбранные статистики
    :return: None
    """
    user = msg.get('from_id')
    total_len = 0
    full_text = msg.get('text_entities', [])
    full_text_parts = []
    collect_text_types = need_stat(selected_stats, 'count_text_types')
    collect_programming = need_stat(selected_stats, 'programming_languages_count')
    collect_words = need_stat(selected_stats, 'count_words_by_user')
    collect_letters = need_stat(selected_stats, 'count_letters_by_user')
    collect_digits = need_stat(selected_stats, 'count_digits_by_user')
    collect_emojis = need_stat(selected_stats, 'count_emojis_by_user')
    collect_laugh = need_stat(selected_stats, 'count_laugh')
    collect_smiles = need_stat(selected_stats, 'count_smiles_by_user')
    collect_longest = need_stat(selected_stats, 'longest_msg')
    collect_custom = need_stat(selected_stats, 'custom_phrases_count_by_user') and bool(cleaned_custom_phrases)

    for entity in full_text:
        text = entity.get('text')
        text_type = entity.get('type')
        if text_type == 'pre' and collect_programming:
            programming_languages_count[entity.get('language')] += 1
        if text:
            if collect_longest:
                total_len += len(text)
            if collect_text_types:
                count_text_types[text_type] += 1
            if text_type in TEXT_TYPES_FOR_WORDS:
                full_text_parts.append(text)

    full_text_str = ''.join(full_text_parts)

    if collect_longest:
        longest_msg.append((msg.get('id'), total_len))

    if collect_smiles:
        count_smiles_by_user[user] += (((full_text_str.count(')') -
                                         full_text_str.count('(')) +
                                        full_text_str.count(':d')))

    if not any((collect_words, collect_letters, collect_digits, collect_emojis, collect_laugh, collect_custom)):
        return

    result = clean_text(full_text_str)

    if collect_custom:
        count_custom_phrases(result, user)

    for word in result.split():
        if collect_words:
            count_words_by_user[word]['total'] += 1
            count_words_by_user[word][user] += 1

        if collect_laugh and is_laugh(word):
            count_laugh[word] += 1

        if not any((collect_letters, collect_digits, collect_emojis)):
            continue

        for symbol in regex.findall(r'\X', word):
            if symbol.isalpha():
                if collect_letters:
                    count_letters_by_user[symbol]['total'] += 1
                    count_letters_by_user[symbol][user] += 1
            elif symbol.isdigit():
                if collect_digits:
                    count_digits_by_user[symbol]['total'] += 1
                    count_digits_by_user[symbol][user] += 1
            elif collect_emojis and is_emoji(symbol):
                count_emojis_by_user[symbol]['total'] += 1
                count_emojis_by_user[symbol][user] += 1


def get_users_stats(users: dict, stats_names: list, *args) -> dict:
    """
    Составляет карточки пользователей (id пользователя -> статистика)
    :param stats_names: названия статистик в *args
    :param users: словарь пользователей
    :param args: статистики
    :return: словарь, где каждому пользователю соответствует словарь с его статистикой
    """
    global users_stats
    users_stats.clear()
    for user in users:
        for name, stat in zip(stats_names, args):
            users_stats[user][name] = stat[user]

    return users_stats


def main(chat_path: str, custom_phrases: list[str] | None = None,
         selected_stats: list[str] | set[str] | None = None) -> dict:
    """
    Запускает анализ чата
    :param selected_stats: выбранные статистики
    :param chat_path: информация о чате в формате json
    :param custom_phrases: список фраз для дополнительного поиска
    :return: словарь со статистиками
    """
    reset_stats()
    selected_stats = normalize_selected_stats(selected_stats)

    if need_stat(selected_stats, 'users_stats'):
        selected_stats |= {
            'count_msgs_by_user',
            'count_total_reactions_by_user',
            'count_photos_by_user',
            'count_videos_by_user',
            'count_stickers_by_user',
            'count_files_by_user',
            'count_voice_msgs_by_user',
            'count_video_msgs_by_user',
            'count_gifs_by_user',
            'count_audios_by_user',
            'count_smiles_by_user',
            'count_locations_by_user',
            'count_contacts_by_user',
            'count_polls_by_user',
            'count_edited_by_user',
            'count_forwarded_by_user',
            'count_replies_by_user',
        }

    for phrase in custom_phrases or []:
        cleaned_phrase = ' '.join(clean_text(phrase).split())
        if cleaned_phrase:
            cleaned_custom_phrases.append(cleaned_phrase)

    result_path = Path(chat_path) / 'result.json'
    with open(result_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data["messages"]
    for msg in messages:

        if msg.get("type") == "message":

            user_id = msg.get('from_id')
            name = msg.get('from', "unknown")
            if user_id and name:
                users[user_id] = name

            if need_stat(selected_stats, 'count_msgs_by_user'):
                count_msgs_by_user[user_id] += 1

            if msg.get('text_entities') and selected_stats & TEXT_STAT_KEYS:
                parse_text(msg, selected_stats)

            if msg.get('reactions') and selected_stats & {
                'count_reactions_by_user',
                'count_total_reactions_by_user',
                'most_reacted',
            }:
                parse_reactions(msg, selected_stats)

            if msg.get('photo'):
                parse_photo(msg, selected_stats)

            if msg.get('file'):
                parse_media(msg, selected_stats)

            if msg.get('edited') and need_stat(selected_stats, 'count_edited_by_user'):
                count_edited_by_user[user_id] += 1

            if msg.get('reply_to_message_id'):
                if need_stat(selected_stats, 'count_replies_by_user'):
                    count_replies_by_user[user_id] += 1
                if need_stat(selected_stats, 'msgs_by_replies_count'):
                    msgs_by_replies_count[msg.get('reply_to_message_id')] += 1

            if need_stat(selected_stats, 'count_by_day') or need_stat(selected_stats, 'locations') or need_stat(
                    selected_stats, 'count_locations_by_user'):
                date = datetime.fromisoformat(msg["date"])

                if need_stat(selected_stats, 'count_by_day'):
                    count_by_day[date.date()] += 1

                if msg.get('location_information'):
                    if need_stat(selected_stats, 'count_locations_by_user'):
                        count_locations_by_user[user_id] += 1
                    if need_stat(selected_stats, 'locations'):
                        locations.append((
                            user_id,
                            msg.get('location_information').get('latitude'),
                            msg.get('location_information').get('longitude'),
                            date))

            if msg.get('contact_information') and need_stat(selected_stats, 'count_contacts_by_user'):
                count_contacts_by_user[user_id] += 1

            if msg.get('poll') and need_stat(selected_stats, 'count_polls_by_user'):
                count_polls_by_user[user_id] += 1

            if msg.get('via_bot') and need_stat(selected_stats, 'count_via_by_user'):
                count_via_by_user[msg.get('via_bot')]['total'] += 1
                count_via_by_user[msg.get('via_bot')][user_id] += 1

            if msg.get('forwarded_from'):
                if need_stat(selected_stats, 'count_forwarded_by_user'):
                    count_forwarded_by_user[user_id] += 1
                if need_stat(selected_stats, 'forwarded_from_count'):
                    forwarded_from_count[msg.get('forwarded_from')] += 1

        elif need_stat(selected_stats, 'service_action_dict'):
            parse_service_msg(msg)

    for stat_key, rows in SORTABLE_LIST_STATS.items():
        if need_stat(selected_stats, stat_key):
            rows.sort(key=lambda x: x[1], reverse=True)

    if need_stat(selected_stats, 'users_stats'):
        get_users_stats(
            users,
            [
                'messages',
                'reactions',
                'photos',
                'videos',
                'stickers',
                'files',
                'voice_messages',
                'video_messages',
                'gifs',
                'audios',
                'smiles',
                'locations',
                'contacts',
                'polls',
                'edited',
                'forwarded',
                'replies',
            ],
            count_msgs_by_user,
            count_total_reactions_by_user,
            count_photos_by_user,
            count_videos_by_user,
            count_stickers_by_user,
            count_files_by_user,
            count_voice_msgs_by_user,
            count_video_msgs_by_user,
            count_gifs_by_user,
            count_audios_by_user,
            count_smiles_by_user,
            count_locations_by_user,
            count_contacts_by_user,
            count_polls_by_user,
            count_edited_by_user,
            count_forwarded_by_user,
            count_replies_by_user,
        )

    return get_stats(selected_stats)
