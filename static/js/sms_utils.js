export function isCodeEmpty(code, errorMessageElement) {
    if (code === "") {
        errorMessageElement.style.display = "block";
        return true;
    }
    return false;
}

export function handleConfirmationCode(code, token, user_id, errorMessageElement, onSuccess) {
    if (window.confirmationResult) {
        window.confirmationResult.confirm(code)
            .then(function (result) {
                errorMessageElement.style.display = "none";
                onSuccess(result.user);
            })
            .catch(function () {
                displayError(errorMessageElement, "Code SMS invalide. Veuillez réessayer.");
            });
    } else {
        displayError(errorMessageElement, "Erreur: impossible de vérifier le code. Veuillez réessayer.");
    }
}

function displayError(element, message) {
    element.textContent = message;
    element.style.display = "block";
}