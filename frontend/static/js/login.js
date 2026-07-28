document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const errorBox = document.getElementById("loginError");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        errorBox.classList.add("hidden");
        errorBox.textContent = "";

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        try {
            const response = await fetch("/frontend-api/login", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username,
                    password,
                }),
            });

            if (!response.ok) {
                const detail = await readErrorDetail(response);
                throw new Error(detail);
            }

            window.location.href = "/clients";
        } catch (error) {
            errorBox.textContent = `Ошибка входа: ${error.message}`;
            errorBox.classList.remove("hidden");
        }
    });
});


async function readErrorDetail(response) {
    try {
        const data = await response.json();

        if (typeof data.detail === "string") {
            return data.detail;
        }

        if (data.detail) {
            return JSON.stringify(data.detail);
        }

        return JSON.stringify(data);
    } catch (_error) {
        return await response.text();
    }
}
