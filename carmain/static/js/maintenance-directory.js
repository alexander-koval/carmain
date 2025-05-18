// maintenance-directory.js


// Функция показа Bootstrap Toast уведомления
function showToast(title, message, type = 'success') {
    const toastElement = $('#notificationToast');
    const toastTitle = $('#toastTitle');
    const toastBody = $('#toastBody');

    toastTitle.text(title);
    toastBody.text(message);

    // Сброс кастомных классов (если используются)
    toastElement.removeClass('toast-success toast-error');
    if (type === 'success') {
        // toastElement.addClass('toast-success');
    } else if (type === 'error') {
        // toastElement.addClass('toast-error');
        toastTitle.text('Ошибка');
    }

    toastElement.toast('show');
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

