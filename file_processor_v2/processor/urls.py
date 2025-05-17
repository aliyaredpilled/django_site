from django.urls import path
from . import views # Импортируем наши views из текущего приложения
import uuid # Нам понадобится uuid для конвертера пути

# Это имя пространства имен URL-адресов для нашего приложения.
# Оно полезно, чтобы избегать конфликтов имен URL, если у нас будет много приложений.
# И чтобы в шаблонах можно было ссылаться на URL типа: {% url 'processor:upload_page' %}
app_name = 'processor'

urlpatterns = [
    # Маршрут для нашей страницы загрузки.
    # Когда пользователь зайдет на /processing/ (или /processing/upload/, как решим),
    # будет вызвана функция upload_page_view из views.py.
    # name='upload_page' - это имя маршрута, по которому к нему можно будет обращаться из кода (например, для redirect).
    path('', views.upload_page_view, name='upload_page'), 
    # Или можно сделать path('upload/', views.upload_page_view, name='upload_page'), тогда адрес будет /processing/upload/
    # Давай пока оставим пустым (''), чтобы страница была доступна по /processing/
    
    # Новый маршрут для API статуса задачи
    # Он будет принимать UUID задачи в URL
    # Например: /processing/task-status/a1b2c3d4-e5f6-7890-1234-567890abcdef/
    path('task-status/<uuid:task_uuid>/', views.task_status_api_view, name='task_status_api'),
] 