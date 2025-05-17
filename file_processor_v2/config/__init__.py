# Этот файл делает папку config Python-пакетом

# Импортируем приложение Celery, чтобы оно было загружено при старте Django
from .celery import app as celery_app

__all__ = ('celery_app',)
