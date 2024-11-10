
# Используйте официальный образ Python в качестве базового образа
FROM python:3.11-slim

# Установите cron
RUN apt-get update && apt-get install -y cron

RUN mkdir "bot_dir"

# Скопируйте requirements.txt и установите зависимости
COPY requirements.txt /bot_dir/requirements.txt

RUN pip install --no-cache-dir -r /bot_dir/requirements.txt

# Скопируйте ваш скрипт в контейнер
COPY . /bot_dir

# Скопируйте crontab файл в контейнер
COPY crontab /etc/cron.d/my-cron-job

# Дайте crontab файлу необходимые права доступа
RUN chmod 0644 /etc/cron.d/my-cron-job

# Примените crontab и запустите cron
RUN crontab /etc/cron.d/my-cron-job

# Создайте log файл для cron
RUN touch /var/log/cron.log

# Запустите cron и оставьте контейнер запущенным
CMD cron && tail -f /var/log/cron.log
