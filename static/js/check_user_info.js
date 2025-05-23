import {
    isCodeEmpty,
    handleConfirmationCode,
} from './sms_utils.js';

document.getElementById("smsForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const code = document.getElementById("inputCode").value;
    const user_id = document.getElementById("userId").value;
    const token = document.getElementById("token").value;
    const errorMessage = document.getElementById("error-message");

    if (isCodeEmpty(code, errorMessage)) return;

    const device_id = generateStableDeviceId()

    // Check the code with Firebase
    handleConfirmationCode(code, token, user_id, errorMessage, function() {
        window.location.href = "/checkphone/" + token + "?user_id=" + user_id + "&device_id=" + device_id;
    });

});

document.getElementById("resend_button").addEventListener("click", function(event) {
    event.preventDefault();

    const user_id = document.getElementById("userId").value;

    alert("La page va se recharger et un nouveau code va t'être envoyé");
    window.location.href = "/checkmail/resend_phone?&user_id="+ user_id;
});


function generateStableDeviceId() {
    const fingerprint = [
        navigator.userAgent,
        navigator.hardwareConcurrency,
        navigator.deviceMemory || "unknown",
        screen.width + "x" + screen.height,
    ].join("||");

    return btoa(fingerprint);
}
