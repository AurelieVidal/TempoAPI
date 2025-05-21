import {
    isCodeEmpty,
    handleConfirmationCode,
} from './sms_utils.js';

document.getElementById("smsForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const code = document.getElementById("inputCode").value;
    const token = document.getElementById("token").value;
    const user_id = document.getElementById("userId").value;
    const errorMessage = document.getElementById("error-message");

    if (isCodeEmpty(code, errorMessage)) return;

    // Check the code with Firebase
    handleConfirmationCode(code, token, user_id, errorMessage, function() {
        window.location.href = "/checkphone/forgotten-password?user_id=" + user_id + "&token=" + token;
    });
});

document.getElementById("resend_button").addEventListener("click", function(event) {
    event.preventDefault();
    const user_id = document.getElementById("userId").value;
    alert("La page va se recharger et un nouveau code va t'être envoyé");
    window.location.href = "/checkmail/forgotten-password/resend_phone?&user_id="+ user_id;
});
