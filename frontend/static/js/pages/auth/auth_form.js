// Utilidad compartida para validación inline y estado de envío en formularios de autenticación.

(() => {
  window.AUTH_EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  window.initAuthForm = ({ form, orderedInputs, getErrorMessage, loadingText, onAfterValidate }) => {
    if (!form) return;

    form.noValidate = true;

    const passwordHint = form.querySelector("#password-hint");
    const submitBtn = form.querySelector('button[type="submit"]');
    const defaultSubmitText = submitBtn ? submitBtn.textContent.trim() : "";
    const textInputs = orderedInputs.filter((input) => input.type !== "checkbox");
    const touched = new Set();
    let submitted = false;
    let submitting = false;

    const setLoading = (activo) => {
      submitting = activo;
      form.classList.toggle("login-form--loading", activo);
      form.querySelectorAll(".login-field").forEach((box) => {
        box.classList.toggle("login-field--disabled", activo);
      });
      // Usar readOnly y clase visual para no excluir valores (incluidos checkboxes) del POST.
      textInputs.forEach((input) => {
        input.readOnly = activo;
      });
      if (submitBtn) {
        submitBtn.classList.toggle("login-submit--loading", activo);
        submitBtn.setAttribute("aria-busy", String(activo));
        submitBtn.textContent = activo && loadingText ? loadingText : defaultSubmitText;
        if (activo) {
          window.setTimeout(() => {
            if (submitting) submitBtn.disabled = true;
          }, 0);
        } else {
          submitBtn.disabled = false;
        }
      }
    };

    window.addEventListener("pageshow", () => {
      if (submitting) {
        setLoading(false);
      }
    });

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
        if (input.id === "password" && passwordHint) passwordHint.hidden = true;
        if (errorEl) {
          errorEl.textContent = errorMessage;
          errorEl.hidden = false;
        }
      } else {
        input.removeAttribute("aria-invalid");
        if (fieldBox) fieldBox.classList.remove("login-field--invalid");
        if (rememberBox) rememberBox.classList.remove("login-remember--invalid");
        if (group) group.classList.remove("login-field-group--invalid");
        if (input.id === "password" && passwordHint) passwordHint.hidden = false;
        if (errorEl) {
          errorEl.hidden = true;
        }
      }

      return !isInvalid;
    };

    const validateField = (input) => {
      if (!input) return true;
      return setFieldState(input, getErrorMessage(input));
    };

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
        if (onAfterValidate) {
          onAfterValidate(input, { submitted, touched, validateField });
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
        if (onAfterValidate) {
          onAfterValidate(input, { submitted, touched, validateField });
        }
      });
    });

    form.addEventListener("submit", (event) => {
      if (submitting) {
        event.preventDefault();
        return;
      }

      submitted = true;
      let firstInvalid = null;

      orderedInputs.forEach((input) => {
        touched.add(input.id);
        if (!validateField(input) && !firstInvalid) {
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
        return;
      }

      setLoading(true);
    });
  };
})();
