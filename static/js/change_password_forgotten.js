import {
    validatePassword,
    getUserInfo,
} from './password_utils.js';

let cpt = 0;

document.getElementById("passwordForm").addEventListener("submit", async function (event) {
    cpt++;

    event.preventDefault();

    const new_password = document.getElementById("newPassword").value.trim();
    const confirm_password = document.getElementById("confirmNewPassword").value.trim();
    const user_id = document.getElementById("userId").value;

    let valid_inputs = await check_inputs(new_password, confirm_password);

    if (!valid_inputs){
        return
    }

    const token = document.getElementById("token").value;
    window.location.href = "/update-password/forgotten-password/" + token + "?user_id=" + user_id + "&new_password=" + new_password;
});


document.getElementById("newPassword").addEventListener("input", async function() {
    if (cpt == 0) return;

    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(new_password, confirm_password);
});

document.getElementById("confirmNewPassword").addEventListener("input", async function() {
    if (cpt == 0) return;

    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(new_password, confirm_password);
});

async function check_inputs(new_password, confirm_password) {
    const errorMessage = document.getElementById("error-message");
    const passwordMessage = document.getElementById("password-message");

    if (!new_password || !confirm_password) {
        errorMessage.textContent = "Tous les champs ne sont pas remplis";
        errorMessage.style.display = "block";
        highlightField("newPassword", new_password, "toggleNewPassword");
        highlightField("confirmNewPassword", confirm_password, "toggleConfirmPassword");
        return false;
    }

    resetField("newPassword", "toggleNewPassword");
    resetField("confirmNewPassword", "toggleConfirmPassword");

    const passwordErrors = await validatePassword(new_password, document.getElementById("username").value, document.getElementById("email").value);

    if (passwordErrors.length > 0) {
        passwordMessage.innerHTML = passwordErrors.join("<br>");
        passwordMessage.style.display = "block";
        highlightField("newPassword", false, "toggleNewPassword");
        return false;
    } else {
        passwordMessage.style.display = "none";
    }

    if (new_password !== confirm_password) {
        errorMessage.textContent = "Les deux nouveaux mots de passe ne correspondent pas...";
        errorMessage.style.display = "block";
        highlightField("confirmNewPassword", false, "toggleConfirmPassword");
        return false;
    }

    errorMessage.style.display = "none";
    return true;
}


function highlightField(fieldId, isValid, toggleId = null) {
    const field = document.getElementById(fieldId);
    const color = isValid ? "#6568F0" : "#F065A6";

    field.style.border = `2px solid ${color}`;
    field.style.borderBottom = `7px solid ${color}`;
    field.style.color = color;

    if (toggleId) {
        document.getElementById(toggleId).style.color = color;
    }
}

function resetField(fieldId, toggleId = null) {
    highlightField(fieldId, true, toggleId);
}

function generateStableDeviceId() {
    const fingerprint = [
        navigator.platform,
        navigator.hardwareConcurrency,
        navigator.deviceMemory || "unknown",
        screen.width + "x" + screen.height,
    ].join("||");

    return btoa(fingerprint);
}
