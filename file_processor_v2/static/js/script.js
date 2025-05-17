document.addEventListener('DOMContentLoaded', function() {
    console.log("script.js загружен и готов к работе!");

    const processorTypeSelect = document.getElementById('id_processor_type');
    const turboSubtypeDiv = document.getElementById('div_id_turbo_smetchik_subtype'); // Предполагаем, что Django Crispy Forms создает такой id
    const taskInfoDiv = document.getElementById('task-info'); // ID для блока с технической информацией
    const celeryInfoDiv = document.getElementById('celery-info'); // ID для блока с Celery ID

    function toggleTurboSubtype() {
        if (processorTypeSelect && turboSubtypeDiv) {
            if (processorTypeSelect.value === 'turbosmetchik') {
                turboSubtypeDiv.style.display = ''; // Показываем
            } else {
                turboSubtypeDiv.style.display = 'none'; // Скрываем
            }
        }
    }

    // Скрываем техническую информацию
    if (taskInfoDiv) {
        // taskInfoDiv.style.display = 'none'; // Раскомментируй, если хочешь полностью скрыть
        // или можно удалить конкретные p теги, если они имеют свои id или классы
        const taskP = taskInfoDiv.querySelector('p:nth-child(1)'); // Пример: первый p
        if (taskP && taskP.textContent.includes('ID Задачи:')) {
            taskP.style.display = 'none';
        }
    }
    if (celeryInfoDiv) { // Если ID задачи и Celery ID в разных блоках
        // celeryInfoDiv.style.display = 'none';  // Раскомментируй, если хочешь полностью скрыть
        const celeryP = celeryInfoDiv.querySelector('p:nth-child(1)'); // Пример: первый p
        if (celeryP && celeryP.textContent.includes('Celery ID:')) {
            celeryP.style.display = 'none';
        }
    }

    // Или если оба ID в одном блоке с результатами, можно пройтись по всем <p> в нем
    const resultBlock = document.getElementById('processing-result'); // Предположим, у блока результатов есть такой id
    if (resultBlock) {
        const paragraphs = resultBlock.getElementsByTagName('p');
        for (let p of paragraphs) {
            if (p.textContent.includes('ID Задачи:') || p.textContent.includes('Celery ID:')) {
                p.style.display = 'none';
            }
        }
    }


    if (processorTypeSelect) {
        processorTypeSelect.addEventListener('change', toggleTurboSubtype);
        // Вызываем функцию при загрузке страницы, чтобы установить правильное начальное состояние
        toggleTurboSubtype();
    }
}); 