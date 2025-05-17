from django import forms

PROCESSOR_CHOICES = [
    ('smeta_ru', 'Смета ру'),
    ('grand_smeta', 'Грандсмета'),
    ('turbosmetchik', 'Турбосметчик'),
]

TURBOSMETCHIK_SUBTYPES = [
    ('turbosmetchik_1', 'Турбосметчик-1'),
    ('turbosmetchik_2', 'Турбосметчик-2'),
    ('turbosmetchik_3', 'Турбосметчик-3'),
]

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Выберите файл (таблица или zip-архив с таблицами)')
    processor_type = forms.ChoiceField(label='Тип сметы', choices=PROCESSOR_CHOICES)
    # Пока сделаем подтип обычным полем, логику его зависимости от processor_type добавим позже
    sub_type = forms.ChoiceField(label='Подтип для Турбосметчика', choices=TURBOSMETCHIK_SUBTYPES, required=False)

    # Если захотим более сложную логику (например, чтобы sub_type был обязательным только для Турбосметчика),
    # можно будет добавить метод clean() сюда. 