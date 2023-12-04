import os
import requests
import json
import vk_api

# Настройки VK API
vk_personal_id = '' # ваш ID ВКонтакте. Обязателен для работы программы

# Настройки Яндекс.Диска
yandex_disk_folder = 'photos' # ваша папка на яндексДиске, куда заливать фото

if not (os.path.isfile("yandex_token.txt") and os.path.isfile("vk_token.txt")):
    print("You need to create files 'yandex_token.txt' and 'vk_token.txt' in program root directory and insert "
          "token from yandex and vk to this files.")
    exit(1)

if len(vk_personal_id) == 0:
    print("You need to set your vk personal id to variable in the main.py file.")
    exit(1)

with open("yandex_token.txt", 'r') as f:
    yandex_disk_token = f.read()

with open("vk_token.txt", 'r') as f:
    vk_token = f.read()

# Инициализация VK API
vk_session = vk_api.VkApi(token=vk_token)
vk_api = vk_session.get_api()


# upload = vk_api.VkUpload(vk_session)

# Создание папки на Яндекс.Диске, если её нет
def create_folder_on_yandex_disk(folder_name, token):
    headers = {'Authorization': f'OAuth {token}'}
    url = f'https://cloud-api.yandex.net/v1/disk/resources?path={folder_name}'
    response = requests.put(url, headers=headers)
    return response.json()


create_folder_on_yandex_disk(yandex_disk_folder, yandex_disk_token)


# Получение фотографий с профиля
def get_photos_from_vk(vk_api, owner_id, count=5):
    photos = vk_api.photos.get(owner_id=owner_id, album_id='profile', count=count, photo_sizes=1)['items']
    return photos


# Сохранение фотографии на Яндекс.Диск
def save_photo_to_yandex_disk(photo_url, yandex_disk_token, folder_name, file_name):
    headers = {'Authorization': f'OAuth {yandex_disk_token}'}
    # save photo from vk by link
    response = requests.get(photo_url)

    with open(file_name, 'wb') as file:
        file.write(response.content)
    # save photo from vk by link end

    # get url for upload from yandex.disk: https://yandex.ru/dev/disk/api/reference/upload.html
    # https://cloud-api.yandex.net/v1/disk/resources/upload
    #  ? path=<путь, по которому следует загрузить файл>
    #  & [overwrite=<признак перезаписи>]
    #  & [fields=<свойства, которые нужно включить в ответ>]

    try:
        url = f'https://cloud-api.yandex.net/v1/disk/resources/upload?path={folder_name}/{file_name}&overwrite=true'
        response = requests.get(url, headers=headers)
        link_to_upload_file = response.json()["href"]
        headers = {
            'Content-Type': 'application/octet-stream'
        }

        # Read the file contents
        with open(file_name, 'rb') as f:
            file_contents = f.read()
            response = requests.put(link_to_upload_file, headers=headers, data=file_contents)

            # Check the response status code
            if response.status_code == 201:
                print('File uploaded successfully to Yandex Disk!')
            else:
                print('Error uploading file to Yandex Disk. Status code is' + str(response.status_code))
    finally:
        os.remove(file_name)  # в любом непредвиденном случае удаляем файлы, чтобы не засорять место на диске


# Получение лайков для фотографии
def get_likes_count(vk_api, owner_id, item_id):
    likes = vk_api.likes.getList(type='photo', owner_id=owner_id, item_id=item_id, filter='likes')['count']
    return likes


# Основной код
def __main__():
    owner_id = int(vk_personal_id)

    photos = get_photos_from_vk(vk_api, owner_id)

    result_data = []

    for photo in photos:
        photo_url = photo['sizes'][-1]['url']
        likes_count = get_likes_count(vk_api, owner_id, photo['id'])
        file_name = f"{likes_count}_likes.jpg"

        save_photo_to_yandex_disk(photo_url, yandex_disk_token, yandex_disk_folder, file_name)

        photo_data = {
            'file_name': file_name,
            'likes_count': likes_count,
            'photo_url': photo_url
        }

        result_data.append(photo_data)

    # Сохранение информации в JSON-файл
    with open('requests.json', 'w', encoding='utf-8') as json_file:
        json.dump(result_data, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    __main__()
print('photos downloaded')
