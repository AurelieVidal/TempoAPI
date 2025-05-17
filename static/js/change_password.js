function togglePasswordVisibility(inputId, iconElement) {
    let input = document.getElementById(inputId);
    let icon = iconElement.querySelector("i");

    if (input.type === "password") {
        input.type = "text";
        icon.classList.replace("fa-eye", "fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.replace("fa-eye-slash", "fa-eye");
    }
}

let cpt = 0;

document.getElementById("passwordForm").addEventListener("submit", async function (event) {
    cpt++;

    event.preventDefault();

    const username = document.getElementById("usernameInput").value.trim();
    const old_password = document.getElementById("passwordInput").value.trim();
    const new_password = document.getElementById("newPassword").value.trim();
    const confirm_password = document.getElementById("confirmNewPassword").value.trim();
    const user_id = document.getElementById("userId").value;

    valid_inputs = await check_inputs(username, old_password, new_password, confirm_password);

    if (valid_inputs == false){
        return
    }

    const credentials = btoa(`${username}:${old_password}`);
    device_id = generateStableDeviceId()

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
                errorMessage.textContent = "Ton nouveau de passe ne semble pas assez sécurisé, essaye de créer un mot de passe un peu plus complexe";
                errorMessage.style.display = "block";
                break;

            case 401:
                if (data["detail"]== "Provided authorization is not valid"){
                    errorMessage.textContent = "Les identifiants ne sont pas valides, vérifie ton mot de passe";
                    errorMessage.style.display = "block";
                    return
                }

                if(data["message"] == "suspicious connexion"){
                    const errorMessage = document.getElementById("error-message");
                    errorMessage.textContent = "Connexion suspicieuse, nous t'avons envoyé un mail pour que tu confirme ton identité, tu pourra ensuite retourner sur cette page";
                    errorMessage.style.display = "block";
                    return
                }
                break;

            default:
                window.location.href = "/redirect/ERROR";
                break;
        }
    } catch (error) {
        window.location.href = "/redirect/ERROR";
    }
});


document.getElementById("usernameInput").addEventListener("input", async function() {
    if (cpt == 0) return;

    const username = document.getElementById("usernameInput").value;
    const old_password = document.getElementById("passwordInput").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(username, old_password, new_password, confirm_password);
});


document.getElementById("passwordInput").addEventListener("input", async function() {
    if (cpt == 0) return;

    const username = document.getElementById("usernameInput").value;
    const old_password = document.getElementById("passwordInput").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(username, old_password, new_password, confirm_password);
});

document.getElementById("newPassword").addEventListener("input", async function() {
    if (cpt == 0) return;

    const username = document.getElementById("usernameInput").value;
    const old_password = document.getElementById("passwordInput").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(username, old_password, new_password, confirm_password);
});

document.getElementById("confirmNewPassword").addEventListener("input", async function() {
    if (cpt == 0) return;

    const username = document.getElementById("usernameInput").value;
    const old_password = document.getElementById("passwordInput").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm_password = document.getElementById("confirmNewPassword").value;

    await check_inputs(username, old_password, new_password, confirm_password);
});

async function check_inputs(username, old_password, new_password, confirm_password) {
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

    const passwordErrors = await validatePassword(new_password, username);
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

async function validatePassword(password, username, email) {
    const errors = [];

    if (password.length < 10) {
        errors.push("Le mot de passe doit contenir au moins 10 caractères.");
    }

    if (/(.)\1\1/.test(password)) {
        errors.push("Le mot de passe ne peut pas contenir trois caractères identiques à la suite.");
    }

    for (let i = 0; i < password.length - 2; i++) {
        const first = password.charCodeAt(i);
        const second = password.charCodeAt(i + 1);
        const third = password.charCodeAt(i + 2);

        if (second - first === 1 && third - second === 1) {
            errors.push("Le mot de passe ne doit pas contenir de séquences de plus de 3 caractères.");
            break;
        }
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/[0-9]/.test(password)) {
        errors.push("Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre.");
    }

    const personalInfoSet = getUserInfo(username, email);
    const passwordLower = password.toLowerCase();
    for (const item of personalInfoSet) {
        if (passwordLower.includes(item)) {
            errors.push("Le mot de passe semble contenir des informations personnelles.");
            break;
        }
    }

    const { pwned, error } = await isPasswordPwned(password);
    if (error) {
        errors.push(error);
    } else if (pwned) {
        errors.push("Ce mot de passe est trop courant ou compromis.");
    }

    return errors;
}

function generateSubstrings(input) {
    const substrings = new Set();
    for (let i = 0; i <= input.length - 3; i++) {
        for (let j = i + 3; j <= input.length; j++) {
            substrings.add(input.slice(i, j).toLowerCase());
        }
    }
    return substrings;
}

function getUserInfo(username, email) {
    const emailParts = email.split("@");
    const emailFirstParts = emailParts[0].split(".");
    const emailSecondPart = emailParts[1].split(".")[0];

    let usernameSubstrings = new Set();
    if (username.length >= 3) {
        usernameSubstrings = generateSubstrings(username);
    }

    const emailInfoSubstrings = new Set();
    for (const part of emailFirstParts) {
        const subs = generateSubstrings(part);
        for (const sub of subs) {
            emailInfoSubstrings.add(sub);
        }
    }

    const checkingList = new Set([...usernameSubstrings, ...emailInfoSubstrings, emailSecondPart.toLowerCase()]);
    return checkingList;
}

async function isPasswordPwned(password) {
    const sha1 = await hashPasswordSHA1(password);
    const prefix = sha1.slice(0, 5);
    const suffix = sha1.slice(5);

    try {
        const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`);
        if (!response.ok) {
            return { error: "Erreur lors de la vérification du mot de passe, réessaye plus tard." };
        }

        const data = await response.text();
        const found = data.split("\n").some(line => {
            const [hashSuffix, count] = line.trim().split(":");
            return hashSuffix.toUpperCase() === suffix.toUpperCase();
        });

        return { pwned: found };
    } catch (err) {
        return { error: "Impossible de vérifier la sécurité du mot de passe." };
    }
}

async function hashPasswordSHA1(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest("SHA-1", data);
    return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, "0"))
        .join("")
        .toUpperCase();
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

