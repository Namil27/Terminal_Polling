import json
import os

from telebot import TeleBot
from tokens import *
from func import message_forming


def main():
    """
    Основная функция для отправки сообщений через Telegram бота.
    Читает сохраненные сообщения, пытается отправить их и сохраняет сообщения,
    которые не удалось отправить, для будущих попыток.
    """
    # Получение пути к файлу относительно текущего скрипта
    script_dir = os.path.dirname(__file__)
    chat_id_path = os.path.join(script_dir, "config_files/chat_id.json")
    save_path = os.path.join(script_dir, "data_files/saved_messages.json")

    # Инициализация бота с токеном из tokens.py
    bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

    # Обработка не отправленных ранее сообщений
    with open(save_path, "r") as saved_message_file:
        saved_messages = json.load(saved_message_file)
        # Временный словарь для хранения успешно отправленных сообщений
        _ = {}
        for saved_id in saved_messages.keys():
            response_saved = bot.send_message(
                chat_id=saved_id,
                text=saved_messages[saved_id],
                parse_mode='Markdown',
                disable_web_page_preview=True,
                timeout=20
            )
            # Если сообщение было успешно отправлено, очищаем временный словарь
            if response_saved is not None:
                json.dump(_, saved_message_file)

    # Основная часть программы
    list_of_messages = message_forming()
    save_messages = {}

    # Проверка на первый запуск скрипта
    if list_of_messages is None:
        return "Первый запуск скрипта, сообщения пойдут начиная со второго."

    # Чтение идентификаторов чатов из файла
    with open(chat_id_path, "r") as ids_dict:
        dict_of_chat_ids = json.load(ids_dict)

        # Отправка новых сообщений
        for chat_id, message in list_of_messages:
            if chat_id in dict_of_chat_ids.keys():
                response = bot.send_message(
                    chat_id=dict_of_chat_ids[chat_id],
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                    timeout=20
                )
                # Если сообщение не удалось отправить, сохраняем его для будущей попытки
                if response is None and message != "" or None:
                    save_messages[chat_id] = message

    # Сохранение не отправленных сообщений
    if save_messages != {}:
        with open(save_path, "w") as save_file:
            json.dump(save_messages, save_file)


if __name__ == "__main__":
    main()
