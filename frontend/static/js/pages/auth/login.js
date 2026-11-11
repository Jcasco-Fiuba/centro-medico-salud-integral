// Validación inline y estado de carga del lado del cliente para el inicio de sesión.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-login-form]");
  if (!form || typeof window.initAuthForm !== "function") return;

  const email = form.querySelector("#email");
  const password = form.querySelector("#password");

  const getErrorMessage = (input) => {
    if (!input) return "";
    if (input.id === "email") {
      const valor = input.value.trim();
      if (!valor) return "! Ingresá tu correo electrónico.";
      if (!window.AUTH_EMAIL_REGEX.test(valor)) {
        return "! Ingresá un correo electrónico válido.";
      }
      return "";
    }
    if (input.id === "password") {
      return input.value ? "" : "! Ingresá tu contraseña.";
    }
    return "";
  };

  window.initAuthForm({
    form,
    orderedInputs: [email, password].filter(Boolean),
    getErrorMessage,
    loadingText: "Iniciando sesión...",
  });
});
