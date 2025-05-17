document.getElementById("smsForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const code = document.getElementById("inputCode").value;
    const token = document.getElementById("token").value;
    const user_id = document.getElementById("userId").value;

    const errorMessage = document.getElementById("error-message");
    if (code === "") {
        errorMessage.style.display = "block";
        return;
    }

    // Check the code with Firebase
    if (window.confirmationResult) {
        window.confirmationResult.confirm(code).then(function (result) {
            const user = result.user;
            errorMessage.style.display = "none";
            window.location.href = "/checkphone/forgotten-password?user_id=" + user_id + "&token=" + token;
        }).catch(function (error) {
            errorMessage.textContent = "Code SMS invalide. Veuillez réessayer.";
            errorMessage.style.display = "block";
        });
    } else {
        errorMessage.textContent = "Erreur: impossible de vérifier le code. Veuillez réessayer.";
        errorMessage.style.display = "block";
    }
});

document.getElementById("resend_button").addEventListener("click", function(event) {
    event.preventDefault();
    const user_id = document.getElementById("userId").value;
    alert("La page va se recharger et un nouveau code va t'être envoyé");
    window.location.href = "/checkmail/forgotten-password/resend_phone?&user_id="+ user_id;
});
