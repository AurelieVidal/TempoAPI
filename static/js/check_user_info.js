// Check if the input code is correct
document.getElementById("smsForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const code = document.getElementById("inputCode").value;
    const user_id = document.getElementById("userId").value;

    const errorMessage = document.getElementById("error-message");
    if (code === "") {
        errorMessage.style.display = "block";
        return;
    }

    window.location.href = "/checkphone/" + code + "?user_id=" + user_id;
});

// Resend the text with verification code
document.getElementById("resend_button").addEventListener("click", function(event) {
    event.preventDefault();

    const user_id = document.getElementById("userId").value;

    alert("La page va se recharger et un nouveau code va t'être envoyé");
    window.location.href = "/checkmail/resend_phone?&user_id="+ user_id;
});
