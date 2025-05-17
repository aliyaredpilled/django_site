# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY . /app/

# Открываем порт 8000 для веб-приложения (Django)
EXPOSE 8000

# Команда для запуска gunicorn сервера (можно будет переопределить в docker-compose.yml для celery)
# CMD позаботится о том, чтобы Django был готов принимать запросы
# config.wsgi - это путь к твоему wsgi.py файлу, который связывает gunicorn с Django
# Если твой проект называется не 'config', а, например, 'file_processor_v2', то будет file_processor_v2.wsgi
# Убедись, что папка 'config' (или как она у тебя называется) содержит файл wsgi.py
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"] 