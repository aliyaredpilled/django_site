from django.db import models
import uuid
from django.utils import timezone # Для created_at и updated_at

# Статус обработки
TASK_STATUS_CHOICES = [
    ('PENDING', 'В очереди'),
    ('STARTED', 'Запущена'),
    ('PROGRESS', 'В обработке'),
    ('SUCCESS', 'Успешно завершена'),
    ('FAILURE', 'Ошибка выполнения'),
]

# Типы обработчиков (для выбора пользователем и для логики в задаче)
PROCESSOR_CHOICES = [
    ('smeta_ru', 'Смета ру'),
    ('grand_smeta', 'Грандсмета'),
    ('turbosmetchik', 'Турбосметчик'),
    # Можно добавить другие, если появятся
    ]
    
# Подтипы для Турбосметчика (пример)
TURBOSMETCHIK_SUBTYPES = [
    ('type1', 'Тип 1 для Турбосметчика'),
    ('type2', 'Тип 2 для Турбосметчика'),
    ('type3', 'Тип 3 для Турбосметчика'),
    ('N/A', 'Не применимо / Не выбрано'), # Для случаев, когда это поле не нужно
]

class ProcessingTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_celery_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="ID задачи Celery", db_index=True)
    
    original_file_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Оригинальное имя файла")
    file_path = models.CharField(max_length=1024, verbose_name="Путь к сохраненному файлу") 

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='PENDING',
        verbose_name="Статус задачи"
    )
    processor_type = models.CharField(
        max_length=50,
        choices=PROCESSOR_CHOICES,
        verbose_name="Тип обработчика",
        null=True, blank=True # Сделаем их пока необязательными на уровне БД
    )
    sub_processor_type = models.CharField(
        max_length=50,
        choices=TURBOSMETCHIK_SUBTYPES,
        verbose_name="Подтип обработчика (если применимо)",
        default='N/A',
        null=True, blank=True
    )

    # Поле для хранения информации о прогрессе (например, current_step, total_steps, message)
    # Используем JSONField, т.к. структура может быть гибкой.
    # Для старых версий Django (до 3.1) может потребоваться установить psycopg2 (для PostgreSQL)
    # или использовать TextField и сериализовать/десериализовать JSON вручную.
    # В Django 3.1+ JSONField работает с SQLite, PostgreSQL, MySQL, Oracle.
    progress_info = models.JSONField(null=True, blank=True, verbose_name="Информация о прогрессе")
    
    # Поле для хранения сообщения о результате (успех/ошибка)
    result_message = models.TextField(null=True, blank=True, verbose_name="Сообщение о результате")

    # Поле для пути к итоговому обработанному файлу
    result_file_path = models.CharField(max_length=1024, null=True, blank=True, verbose_name="Путь к итоговому файлу")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время последнего обновления")

    class Meta:
        verbose_name = "Задача обработки"
        verbose_name_plural = "Задачи обработки"
        ordering = ['-created_at'] # Сортировка по умолчанию - сначала новые

    def __str__(self):
        return f"Задача {self.id} ({self.original_file_name or 'N/A'}) - {self.get_status_display()}"

    def update_progress(self, current, total, status_message):
        self.progress_info = {
            'current': current,
            'total': total,
            'status_message': status_message
        }
        if self.status not in ['SUCCESS', 'FAILURE']:
            self.status = 'PROGRESS'
        # Мы будем вызывать save() в задаче Celery после вызова этого метода,
        # чтобы сгруппировать изменения, если это необходимо.
        # Но для простоты можно и здесь save() вызывать.
        self.save(update_fields=['progress_info', 'status', 'updated_at'])

    def mark_as_failed(self, error_message):
        self.status = 'FAILURE'
        self.result_message = error_message
        current_progress = self.progress_info if isinstance(self.progress_info, dict) else {}
        current_progress['status_message'] = f"Ошибка: {error_message}"
        self.progress_info = current_progress
        self.save(update_fields=['status', 'result_message', 'progress_info', 'updated_at'])

    def mark_as_success(self, success_message, result_file_path_param=None, result_data=None):
        self.status = 'SUCCESS'
        self.result_message = success_message
        if result_file_path_param:
            self.result_file_path = result_file_path_param # Сохраняем путь к файлу
        
        current_progress = self.progress_info if isinstance(self.progress_info, dict) else {}
        if result_data and isinstance(result_data, dict):
            current_progress.update(result_data)
        current_progress['status_message'] = success_message # Убедимся, что финальное сообщение тоже есть
        self.progress_info = current_progress
        self.save(update_fields=['status', 'result_message', 'result_file_path', 'progress_info', 'updated_at'])