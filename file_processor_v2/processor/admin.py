from django.contrib import admin
from .models import ProcessingTask # Импортируем нашу модель

# Register your models here.
admin.site.register(ProcessingTask) # Регистрируем модель
