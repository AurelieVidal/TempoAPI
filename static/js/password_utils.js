export async function validatePassword(password, username, email) {
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

export function getUserInfo(username, email) {
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
