// Validación inline y estado de carga del lado del cliente para el registro de pacientes.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-register-form]");
  if (!form || typeof window.initAuthForm !== "function") return;

  const fields = {
    nombre: form.querySelector("#nombre"),
    apellido: form.querySelector("#apellido"),
    dni: form.querySelector("#dni"),
    email: form.querySelector("#email"),
    password: form.querySelector("#password"),
    repetirPassword: form.querySelector("#repetir-password"),
    terminos: form.querySelector("#terminos"),
  };

  const DNI_REGEX = /^\d{7,8}$/;

  const getErrorMessage = (input) => {
    if (!input) return "";

    switch (input.id) {
      case "nombre":
        return input.value.trim() ? "" : "! Ingresá tu nombre.";
      case "apellido":
        return input.value.trim() ? "" : "! Ingresá tu apellido.";
      case "dni": {
        const valor = input.value.trim();
        if (!valor) return "! Ingresá tu DNI.";
        if (!DNI_REGEX.test(valor)) return "! Ingresá un DNI válido de 7 u 8 números.";
        return "";
      }
      case "email": {
        const valor = input.value.trim();
        if (!valor) return "! Ingresá tu correo electrónico.";
        if (!window.AUTH_EMAIL_REGEX.test(valor)) {
          return "! Ingresá un correo electrónico válido.";
        }
        return "";
      }
      case "password": {
        const valor = input.value;
        if (!valor) return "! Ingresá tu contraseña.";
        if (valor.length < 8) return "! La contraseña debe tener al menos 8 caracteres.";
        return "";
      }
      case "repetir-password": {
        const valor = input.value;
        if (!valor) return "! Repetí tu contraseña.";
        if (fields.password && valor !== fields.password.value) {
          return "! Las contraseñas no coinciden. Volvé a escribirlas.";
        }
        return "";
      }
      case "terminos":
        return input.checked
          ? ""
          : "! Para crear tu cuenta, aceptá los términos y la política de privacidad.";
      default:
        return "";
    }
  };

  window.initAuthForm({
    form,
    orderedInputs: [
      fields.nombre,
      fields.apellido,
      fields.dni,
      fields.email,
      fields.password,
      fields.repetirPassword,
      fields.terminos,
    ].filter(Boolean),
    getErrorMessage,
    loadingText: "Creando cuenta...",
    onAfterValidate: (input, { submitted, touched, validateField }) => {
      if (
        input.id === "password" &&
        fields.repetirPassword &&
        (submitted ||
          touched.has("repetir-password") ||
          fields.repetirPassword.value.length > 0 ||
          fields.repetirPassword.getAttribute("aria-invalid") === "true")
      ) {
        validateField(fields.repetirPassword);
      }
    },
  });
});
