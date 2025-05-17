from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse # <--- Добавляем JsonResponse
from .forms import UploadFileForm
from .tasks import process_uploaded_file
from .models import ProcessingTask # Импортируем нашу модель
# import uuid # Пока не используется явно, можно убрать или оставить
import os # Для работы с путями и файлами
from django.conf import settings # Для доступа к MEDIA_ROOT, если будем сохранять файлы
from django.core.files.storage import FileSystemStorage # <--- Для сохранения файлов
import uuid # Понадобится для проверки task_id
from urllib.parse import urljoin # Для формирования URL
import traceback # Импортируем traceback

def upload_page_view(request):
    task_to_display = None
    # Пытаемся получить ID последней задачи из сессии
    last_task_db_id = request.session.get('last_task_db_id')
    if last_task_db_id:
        try:
            task_to_display = ProcessingTask.objects.get(id=last_task_db_id)
        except ProcessingTask.DoesNotExist:
            # Если задача не найдена (например, удалена), чистим сессию
            request.session.pop('last_task_db_id', None)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            processor_type = form.cleaned_data['processor_type']
            sub_type = form.cleaned_data.get('sub_type') # .get, так как он не обязательный

            # Сохраняем файл
            fs = FileSystemStorage() # Используем хранилище по умолчанию (которое смотрит на MEDIA_ROOT)
            # fs = FileSystemStorage(location=settings.MEDIA_ROOT) # Можно явно указать, но обычно не нужно
            
            # Генерируем имя файла. Можно добавить UUID для уникальности, чтобы не перезаписывать файлы с одинаковыми именами
            # file_name_on_server = str(uuid.uuid4()) + "_" + uploaded_file.name
            # Пока просто используем оригинальное имя. ОСТОРОЖНО: это может перезаписать файлы!
            # Лучше добавить какую-то логику для уникальных имен в будущем.
            file_name_on_server = uploaded_file.name 
            
            actual_filename_saved = fs.save(file_name_on_server, uploaded_file)
            # fs.save возвращает реальное имя файла, под которым он был сохранен (если Django пришлось его изменить для уникальности)
            
            # Получаем полный путь к сохраненному файлу
            saved_file_path = fs.path(actual_filename_saved)
            # saved_file_url = fs.url(actual_filename_saved) # URL файла, если нужно

            # 1. Создаем запись ProcessingTask в базе данных
            # (Предполагаем, что у ProcessingTask есть поля для file_name, processor_type, sub_type и status)
            # Также добавим task_id от Celery, чтобы связать.
            # Пока у нас в модели нет task_id, так что создадим без него, но потом добавим.
            
            # Перед тем как создавать ProcessingTask, нужно убедиться, что в модели есть нужные поля.
            # Давай пока создадим ProcessingTask с тем, что есть, и потом доработаем модель.
            new_task_db_entry = ProcessingTask.objects.create(
                original_file_name=uploaded_file.name, # Сохраняем оригинальное имя
                file_path=saved_file_path,       # Сохраняем ПОЛНЫЙ ПУТЬ к файлу на сервере
                status='PENDING', # Начальный статус
                processor_type=processor_type,
                sub_processor_type=sub_type if sub_type else 'N/A' # Пример
            )

            # 2. Запускаем Celery задачу
            # Передаем ID созданной записи в БД, чтобы Celery задача могла обновлять ее статус
            celery_task_result = process_uploaded_file.delay(
                # Передаем ПОЛНЫЙ ПУТЬ к сохраненному файлу
                file_path=saved_file_path, 
                processor_type=processor_type,
                sub_type=sub_type,
                db_task_id=new_task_db_entry.id # <<< Передаем ID записи из БД
            )
            
            # Сохраняем ID задачи Celery в нашей модели (нужно будет добавить поле task_celery_id в модель)
            new_task_db_entry.task_celery_id = celery_task_result.id
            new_task_db_entry.save()

            # Сохраняем ID созданной задачи в сессию
            request.session['last_task_db_id'] = str(new_task_db_entry.id) # ID в сессию (UUID нужно в строку)

            # Перенаправляем на эту же страницу (GET-запросом)
            return redirect('processor:upload_page') 
    else:
        form = UploadFileForm()
    return render(request, 'processor/upload_page.html', {
        'form': form,
        'task_to_display': task_to_display # Передаем задачу в шаблон
    })

# Новый view для API статуса задачи
def task_status_api_view(request, task_uuid):
    print(f"[DEBUG_VIEWS] task_status_api_view called with task_uuid: {task_uuid} (type: {type(task_uuid)})")
    try:
        # task_uuid УЖЕ является объектом UUID благодаря <uuid:task_uuid> в urls.py
        # task_id = uuid.UUID(task_uuid) # <--- ЭТА СТРОКА БОЛЬШЕ НЕ НУЖНА И УДАЛЕНА
        print(f"[DEBUG_VIEWS] task_uuid is already a UUID object.")
        
        # Используем task_uuid напрямую для поиска
        task = ProcessingTask.objects.get(id=task_uuid) 
        print(f"[DEBUG_VIEWS] Fetched task: {task.id}, status: {task.status}")
        
        progress_data = task.progress_info if isinstance(task.progress_info, dict) else {}

        data = {
            'id': str(task.id),
            'task_celery_id': task.task_celery_id,
            'status': task.status,
            'status_display': task.get_status_display(),
            'progress_info': progress_data, 
            'result_message': task.result_message,
            'original_file_name': task.original_file_name,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'result_file_url': None,
            'result_file_name': None,
        }
        print(f"[DEBUG_VIEWS] Initial data prepared: {data}")

        if task.status == 'SUCCESS':
            print(f"[DEBUG_VIEWS] Task status is SUCCESS. Checking result_file_path.")
            if task.result_file_path:
                print(f"[DEBUG_VIEWS] task.result_file_path: {task.result_file_path}, type: {type(task.result_file_path)}")
                print(f"[DEBUG_VIEWS] settings.MEDIA_ROOT: {settings.MEDIA_ROOT}, type: {type(settings.MEDIA_ROOT)}")
                
                # Убедимся, что оба аргумента для relpath - строки и не None
                path_to_result = str(task.result_file_path) if task.result_file_path is not None else ''
                media_root_path = str(settings.MEDIA_ROOT) if settings.MEDIA_ROOT is not None else ''

                if not path_to_result or not media_root_path:
                    print(f"[DEBUG_VIEWS] Error: path_to_result or media_root_path is empty. Cannot compute relpath.")
                else:
                    relative_path_to_file = os.path.relpath(path_to_result, media_root_path)
                    print(f"[DEBUG_VIEWS] relative_path_to_file: {relative_path_to_file}, type: {type(relative_path_to_file)}")
                    
                    media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else settings.MEDIA_URL + '/'
                    # Используем str() на всякий случай и '/' как разделитель для URL
                    data['result_file_url'] = urljoin(media_url, str(relative_path_to_file).replace('/', '/')) 
                    data['result_file_name'] = os.path.basename(path_to_result)
                    print(f"[DEBUG_VIEWS] result_file_url: {data['result_file_url']}")
            else:
                print(f"[DEBUG_VIEWS] task.result_file_path is None or empty.")
        else:
            print(f"[DEBUG_VIEWS] Task status is not SUCCESS (it is {task.status}). Skipping result file processing.")

        print(f"[DEBUG_VIEWS] Final data to be sent: {data}")
        return JsonResponse(data)
    except Exception as e:
        print(f"[DEBUG_VIEWS_ERROR] An exception occurred in task_status_api_view for task_uuid {task_uuid}:")
        # Печатаем полный traceback вручную
        detailed_traceback = traceback.format_exc()
        print(detailed_traceback)
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}', 'traceback': detailed_traceback}, status=500)
