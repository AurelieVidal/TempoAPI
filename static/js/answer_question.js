document.getElementById("validate_answer").addEventListener("click", async function (event) {
    event.preventDefault();
    const answer = document.getElementById("answer").value;
    const username = document.getElementById("username").value;
    const validationId = document.getElementById("validation_id").value;

    if (!answer) {
        document.getElementById("error-message").textContent = "Tu dois entrer une réponse.";
        return;
    }

    try {
        const response = await fetch(`/security/validate-connection/${username}?validationId=${validationId}&answer=${encodeURIComponent(answer)}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        switch (response.status) {
            case 200:
                window.location.href = "/redirect/SUCCESS";
                break;

            case 403:
                if (data.message.includes("now banned")) {
                    document.getElementById("error-message").textContent = "Trop de tentatives échouées, ton compte est bloqué. Contacte le support.";
                    document.getElementById("error-message").style.display = "block";
                    window.location.href = "/redirect/BANNED";
                } else {
                    document.getElementById("error-message").textContent = "Réponse incorrecte... Essaie encore.";
                    document.getElementById("error-message").style.display = "block";
                }
                break;

            case 404:
                document.getElementById("error-message").textContent = "Tes identifiants sont invalides. As-tu bien cliqué sur le lien envoyé par mail ?";
                document.getElementById("error-message").style.display = "block";
                break;

            case 500:
                document.getElementById("error-message").textContent = "Erreur inattendue. Réessaie plus tard.";
                document.getElementById("error-message").style.display = "block";
                window.location.href = "/redirect/ERROR";
                break;

            default:
                document.getElementById("error-message").textContent = "Une erreur inconnue est survenue.";
                document.getElementById("error-message").style.display = "block";
                window.location.href = "/redirect/ERROR";
                break;
        }
    } catch (error) {
        console.log(`Exception while doing something: ${error}`);
        document.getElementById("error-message").textContent = "Impossible de contacter le serveur.";
        window.location.href = "/redirect/ERROR";
    }
});
