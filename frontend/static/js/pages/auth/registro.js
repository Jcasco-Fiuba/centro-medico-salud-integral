// Validación del lado del cliente para el formulario de registro de pacientes.
// Alcance: valida campos obligatorios, formato de DNI (7 u 8 dígitos),
// formato de correo electrónico, longitud mínima de contraseña (8 caracteres),
// coincidencia entre contraseñas y aceptación de términos. No realiza peticiones
// al backend ni simula respuestas del servidor.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-register-form]");
  if (!form) return;

  form.noValidate = true;

  const fields = {
    nombre: form.querySelector("#nombre"),
    apellido: form.querySelector("#apellido"),
    dni: form.querySelector("#dni"),
    email: form.querySelector("#email"),
    password: form.querySelector("#password"),
    repetirPassword: form.querySelector("#repetir-password"),
    terminos: form.querySelector("#terminos"),
  };

  const passwordHint = form.querySelector("#password-hint");
  const touched = new Set();
  let submitted = false;

  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const DNI_REGEX = /^\d{7,8}$/;

  const getErrorMessage = (input) => {
    if (!input) return "";

    switch (input.id) {
      case "nombre": {
        return input.value.trim() ? "" : "! Ingresá tu nombre.";
      }
      case "apellido": {
        return input.value.trim() ? "" : "! Ingresá tu apellido.";
      }
      case "dni": {
        const valor = input.value.trim();
        if (!valor) return "! Ingresá tu DNI.";
        if (!DNI_REGEX.test(valor)) {
          return "! Ingresá un DNI válido de 7 u 8 números.";
        }
        return "";
      }
      case "email": {
        const valor = input.value.trim();
        if (!valor) return "! Ingresá tu correo electrónico.";
        if (!EMAIL_REGEX.test(valor)) {
          return "! Ingresá un correo electrónico válido.";
        }
        return "";
      }
      case "password": {
        const valor = input.value;
        if (!valor) return "! Ingresá tu contraseña.";
        if (valor.length < 8) {
          return "! La contraseña debe tener al menos 8 caracteres.";
        }
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
      case "terminos": {
        return input.checked
          ? ""
          : "! Para crear tu cuenta, aceptá los términos y la política de privacidad.";
      }
      default:
        return "";
    }
  };

  const setFieldState = (input, errorMessage) => {
    if (!input) return true;

    const group = input.closest(".login-field-group");
    const fieldBox = input.closest(".login-field");
    const rememberBox = input.closest(".login-remember");
    const errorEl = form.querySelector(`#${input.id}-error`);
    const isInvalid = Boolean(errorMessage);

    if (isInvalid) {
      input.setAttribute("aria-invalid", "true");
      if (fieldBox) fieldBox.classList.add("login-field--invalid");
      if (rememberBox) rememberBox.classList.add("login-remember--invalid");
      if (group) group.classList.add("login-field-group--invalid");
      if (input.id === "password" && passwordHint) {
        passwordHint.hidden = true;
      }
      if (errorEl) {
        errorEl.textContent = errorMessage;
        errorEl.hidden = false;
      }
    } else {
      input.removeAttribute("aria-invalid");
      if (fieldBox) fieldBox.classList.remove("login-field--invalid");
      if (rememberBox) rememberBox.classList.remove("login-remember--invalid");
      if (group) group.classList.remove("login-field-group--invalid");
      if (input.id === "password" && passwordHint) {
        passwordHint.hidden = false;
      }
      if (errorEl) {
        errorEl.hidden = true;
      }
    }

    return !isInvalid;
  };

  const validateField = (input) => {
    if (!input) return true;
    const message = getErrorMessage(input);
    return setFieldState(input, message);
  };

  const orderedInputs = [
    fields.nombre,
    fields.apellido,
    fields.dni,
    fields.email,
    fields.password,
    fields.repetirPassword,
    fields.terminos,
  ].filter(Boolean);

  orderedInputs.forEach((input) => {
    if (input.type === "checkbox") {
      input.addEventListener("change", () => {
        touched.add(input.id);
        validateField(input);
      });
      return;
    }

    input.addEventListener("blur", () => {
      touched.add(input.id);
      validateField(input);

      if (
        input.id === "password" &&
        fields.repetirPassword &&
        (touched.has("repetir-password") || fields.repetirPassword.value.length > 0)
      ) {
        validateField(fields.repetirPassword);
      }
    });

    input.addEventListener("input", () => {
      if (
        submitted ||
        touched.has(input.id) ||
        input.getAttribute("aria-invalid") === "true"
      ) {
        validateField(input);
      }

      if (
        input.id === "password" &&
        fields.repetirPassword &&
        (submitted ||
          touched.has("repetir-password") ||
          fields.repetirPassword.getAttribute("aria-invalid") === "true")
      ) {
        validateField(fields.repetirPassword);
      }
    });
  });

  form.addEventListener("submit", (event) => {
    submitted = true;
    let firstInvalid = null;

    orderedInputs.forEach((input) => {
      touched.add(input.id);
      const valid = validateField(input);
      if (!valid && !firstInvalid) {
        firstInvalid = input;
      }
    });

    if (firstInvalid) {
      event.preventDefault();
      firstInvalid.focus();
      return;
    }

    if ((form.getAttribute("action") || "#") === "#") {
      event.preventDefault();
    }
  });
});
