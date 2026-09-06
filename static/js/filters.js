/**
 * Real-time filters with debounce for HR panel candidates table.
 * Selects submit instantly; text inputs debounce 400ms.
 */
(function () {
    const form = document.getElementById("filter-form");
    if (!form) return;

    let debounceTimer = null;

    function submitForm() {
        form.submit();
    }

    function debounceSubmit() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(submitForm, 400);
    }

    // Selects — submit immediately on change
    form.querySelectorAll("select").forEach(function (el) {
        el.addEventListener("change", submitForm);
    });

    // Text inputs — debounce 400ms
    form.querySelectorAll("input[type='text'], input[type='number']").forEach(function (el) {
        el.addEventListener("input", debounceSubmit);
    });
})();
