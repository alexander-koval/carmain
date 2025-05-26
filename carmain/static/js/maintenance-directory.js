// maintenance-directory.js


// Функция показа Bootstrap Toast уведомления
function showToast(title, message, type = 'success') {
    const toastElement = document.getElementById('notificationToast');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');

    toastTitle.textContent = title;
    toastBody.textContent = message;

    // Сброс кастомных классов (если используются)
    toastElement.classList.remove('toast-success', 'toast-error');
    if (type === 'success') {
        // toastElement.classList.add('toast-success');
    } else if (type === 'error') {
        // toastElement.classList.add('toast-error');
        toastTitle.textContent = 'Ошибка';
    }

    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}


document.body.addEventListener('htmx:afterRequest', function(event) {
    const xhr = event.detail.xhr;
    const operationStatus = xhr.getResponseHeader('X-Operation-Status');
    const operationMessage = xhr.getResponseHeader('X-Operation-Message') || 'Операция выполнена.';

    if (event.detail.successful) {
        if (event.detail.requestConfig.verb === 'post') {
            showToast('Успех', operationMessage, 'success');
        }
    } else {
        const errorMessage = xhr.responseText || 'Произошла ошибка при выполнении операции.';
        showToast('Ошибка', errorMessage, 'error');
    }
});


document.body.addEventListener('htmx:responseError', function(event) {
    console.error('HTMX Response Error:', event.detail.error);
    const xhr = event.detail.xhr;
    const errorMessage = xhr.responseText || 'Ошибка сети или сервера.';
    showToast('Ошибка запроса', errorMessage, 'error');
});

