import json
import requests
import os


def search_info_units() -> dict or None:
    """
    Получает список инфоповодов от API и сохраняет их в файл. Возвращает словарь новых инфоповодов.

    :return: Словарь новых инфоповодов или None в случае ошибки.
    """
    script_dir = os.path.dirname(__file__)
    token_path = os.path.join(script_dir, "config_files/bearer_token.json")
    api_urls_path = os.path.join(script_dir, "config_files/api_urls.json")
    info_units_path = os.path.join(script_dir, "data_files/old_info_units.json")

    with open(api_urls_path, "r") as api_urls_file:
        endpoint_url = json.load(api_urls_file)["info-units"]

    with open(token_path, "r") as bearer_token_file:
        headers = json.load(bearer_token_file)

        # Забираем список инфоповодов от API
        try:
            response = requests.get(url=endpoint_url, headers=headers)
            if response.status_code != 200:
                return None
            data = response.json()
            new_info_units = {
                str(item['id']): {
                    "title": item['title'],
                    "urgency": item["urgency"],
                    "embargo": item["embargo"],
                    "medias": {media["id"]: media["title"] for media in item["smi"]},
                    "source": {item["source"]["title"]: item["source"]["id"]}
                }
                for item in data['results']
            }
            with open(info_units_path, 'w', encoding='utf-8') as file:
                json.dump(new_info_units, file, ensure_ascii=False, indent=4)
            return new_info_units
        except Exception as e:
            return f"ERROR: {e}"


def take_old_info_units() -> dict:
    """
    Загружает старые инфоповоды из файла.

    :return: Словарь старых инфоповодов.
    """
    script_dir = os.path.dirname(__file__)
    old_info_units_file_path = os.path.join(script_dir, "data_files/old_info_units.json")

    with open(old_info_units_file_path, "r") as old_info_units_json:
        old_info_units = json.load(old_info_units_json)
    return old_info_units


def new_info_units() -> dict or None:
    """
    Определяет новые инфоповоды, которые отсутствуют в старом списке.

    :return: Словарь новых инфоповодов или None, если старый список пуст.
    """
    old_info_units = take_old_info_units()
    present_info_units = search_info_units()
    if old_info_units == {}:
        return None
    set_of_new_info_units_ids = set(present_info_units.keys()) - set(old_info_units.keys())
    return {id: present_info_units[id] for id in set_of_new_info_units_ids}


def message_forming() -> list[(str, str)] or None:
    """
    Формирует сообщения для новых инфоповодов.

    :return: Список кортежей (media_id, сообщение) или None, если новых инфоповодов нет.
    """
    result = new_info_units()
    if result is None:
        return None
    list_of_info_units_messages = []
    script_dir = os.path.dirname(__file__)
    api_urls_path = os.path.join(script_dir, "config_files/api_urls.json")

    with open(api_urls_path, "r") as info_units_url_file:
        url = json.load(info_units_url_file)["info-unit_link"]

    for id in result:
        for media_id in result[id]["medias"]:
            title = result[id]["title"]
            source = list(result[id]["source"].keys())[0]
            media = result[id]["medias"][media_id]
            media_shielded = media if "." not in media else media.replace(".", ".\u2060")
            urgency = result[id]["urgency"]
            embargo = result[id]["embargo"] if result[id]["embargo"] is not None else "Нет"
            body_message = (
                f'\n***⚠️ {title}***\n'
                f'Новый инфоповод: [ID {id}]({url}{id})\n'
                f'Источник: {source}\n'
                f'СМИ: {media_shielded}\n'
                f'Время отработки: {urgency}\n'
                f'Эмбарго: {embargo}\n'
            )
            result_tuple = (str(media_id), body_message)
            list_of_info_units_messages.append(result_tuple)

    return list_of_info_units_messages


def chat_to_media(id_media_to_id_chat: dict) -> dict:
    """
    Преобразует словарь id_media: id_chat в словарь id_chat: [id_media].

    :param id_media_to_id_chat: Исходный словарь id_media: id_chat.
    :return: Новый словарь id_chat: [id_media].
    """
    # Новый словарь
    id_chat_to_id_media = {}

    # Проход по исходному словарю
    for media_id, chat_id in id_media_to_id_chat.items():
        if chat_id not in id_chat_to_id_media:
            id_chat_to_id_media[chat_id] = []
        id_chat_to_id_media[chat_id].append(media_id)

    return id_chat_to_id_media


def take_token():
    """
    Получает новый токен и сохраняет его в файл bearer_token.json.

    :return: None
    """
    script_dir = os.path.dirname(__file__)
    token_path = os.path.join(script_dir, "config_files/bearer_token.json")
    creds_path = os.path.join(script_dir, "config_files/creds.json")
    api_urls_path = os.path.join(script_dir, "config_files/api_urls.json")
    headers = {
        "Content-Type": "application/json"
    }
    with open(api_urls_path, "r") as urls_file:
        url = json.load(urls_file)["new_token"]

    token_dict = {}

    # Загрузка данных из creds.json
    with open(creds_path, "r") as creds_file:
        creds_data = json.load(creds_file)

    # Отправка запроса
    response = requests.post(url, headers=headers, json=creds_data)

    # Проверка успешного ответа
    if response.status_code == 200:
        response_json = response.json()
        print("Новый токен успешно получен!")
        if "access" in response_json:
            print("Новый токен успешно записан в файл bearer_token.json!")
            bearer_token = "Bearer " + response_json["access"]
            token_dict["Authorization"] = bearer_token

            # Запись токена в файл
            with open(token_path, "w") as token_file:
                json.dump(token_dict, token_file, ensure_ascii=False, indent=4)
        else:
            print("Error: 'access' key not found in the response JSON.")
    else:
        print("Error: Failed to obtain token. Status Code:", response.status_code)
        print("Response Content:", response.content)
