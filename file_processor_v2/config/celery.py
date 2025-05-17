import os
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр приложения Celery
# 'config' - это имя нашего Django-проекта (папки с settings.py)
app = Celery('config')

# Загружаем конфигурацию для Celery из настроек Django (из settings.py)
# Все настройки Celery в settings.py должны начинаться с 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем файлы tasks.py во всех установленных приложениях Django
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 