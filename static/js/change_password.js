import {
    validatePassword,
    highlightField,
    resetField,
    generateStableDeviceId
} from './password_utils.js';

let cpt = 0;

document.addEventListener("DOMContentLoaded", function () {


    const form = document.getElementById("passwordForm");
    if (!form) {
        console.warn("Formulaire introuvable");
        return;
    }

    form.addEventListener("submit", async function (event) {
        cpt++;

        event.preventDefault();

        const username = document.getElementById("usernameInput").value.trim();
        const email = document.getElementById("email").value;
        const old_password = document.getElementById("passwordInput").value.trim();
        const new_password = document.getElementById("newPassword").value.trim();
        const confirm_password = document.getElementById("confirmNewPassword").value.trim();
        const user_id = document.getElementById("userId").value;

        let valid_inputs = await check_inputs(username, old_password, new_password, confirm_password, email);
        if (!valid_inputs) return;

        const credentials = btoa(`${username}:${old_password}`);
        const device_id = generateStableDeviceId();

        const headers = {
            "Accept": "application/json",
            "Authorization": "Basic " + credentials,
            "device": device_id,
            "Content-Type": "application/json"
        };

        const body = JSON.stringify({ "newPassword": new_password });

        try {
            const response = await fetch("/users/" + user_id, {
                method: "PATCH",
                headers: headers,
                body: body
            });

            const data = await response.json();
            const errorMessage = document.getElementById("error-message");

            switch (response.status) {
                case 200:
                    window.location.href = "/redirect/PASSWORD_CHANGED?username=" + encodeURIComponent(username);
                    break;

                case 400:
                    errorMessage.textContent = "Ton nouveau mot de passe ne semble pas assez sécurisé, essaye de créer un mot de passe un peu plus complexe";
                    errorMessage.style.display = "block";
                    break;

                case 401:
                    if (data["detail"] === "Provided authorization is not valid") {
                        errorMessage.textContent = "Les identifiants ne sont pas valides, vérifie ton mot de passe";
                        errorMessage.style.display = "block";
                        return;
                    }
                    if (data["message"] === "suspicious connexion") {
                        errorMessage.textContent = "Connexion suspicieuse, un mail t’a été envoyé pour vérifier ton identité.";
                        errorMessage.style.display = "block";
                        return;
                    }
                    break;

                default:
                    window.location.href = "/redirect/ERROR";
                    break;
            }
        } catch (error) {
            console.log(`Exception while doing something: ${error}`);
            window.location.href = "/redirect/ERROR";
        }
    });
});


const inputIds = ["usernameInput", "passwordInput", "newPassword", "confirmNewPassword"];

async function handleInput() {
    if (cpt === 0) return;

    const username = document.getElementById("usernameInput").value;
    const email = document.getElementById("email").value;
    const old_password = document.getElementById("passwordInput").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(username, old_password, new_password, confirm_password, email);
}

inputIds.forEach(id => {
    document.getElementById(id).addEventListener("input", handleInput);
});

async function check_inputs(username, old_password, new_password, confirm_password, email) {
    console.log("CHECKKK")
    const errorMessage = document.getElementById("error-message");
    const passwordMessage = document.getElementById("password-message");

    if (!username || !old_password || !new_password || !confirm_password) {
        errorMessage.textContent = "Tous les champs ne sont pas remplis";
        errorMessage.style.display = "block";

        highlightField("usernameInput", username);
        highlightField("passwordInput", old_password, "toggleOldPassword");
        highlightField("newPassword", new_password, "toggleNewPassword");
        highlightField("confirmNewPassword", confirm_password, "toggleConfirmPassword");
        return false;
    }

    resetField("usernameInput");
    resetField("passwordInput", "toggleOldPassword");
    resetField("newPassword", "toggleNewPassword");
    resetField("confirmNewPassword", "toggleConfirmPassword");
    errorMessage.style.display = "None";

    const passwordErrors = await validatePassword(new_password, username, email);
    if (passwordErrors.length > 0) {
        passwordMessage.innerHTML = passwordErrors.join("<br>");
        passwordMessage.style.display = "block";
        highlightField("newPassword", false, "toggleNewPassword");
        return false;
    } else {
        passwordMessage.style.display = "none";
    }

    if (old_password === new_password) {
        errorMessage.textContent = "Le nouveau mot de passe ne peut pas être le même que l'ancien";
        errorMessage.style.display = "block";
        highlightField("newPassword", false, "toggleNewPassword");
        return false;
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
