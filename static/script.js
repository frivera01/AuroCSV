document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"]');
    const submitBtn = document.querySelector('.btn-submit');

    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    });

    submitBtn.addEventListener('click', function() {
        submitBtn.textContent = 'Procesando...';
    });
});
