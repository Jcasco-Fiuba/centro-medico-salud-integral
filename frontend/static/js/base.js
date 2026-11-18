// Interacciones compartidas de interfaz. No realizar solicitudes a la API aquí.

window.addEventListener("pageshow", (event) => {
  const body = document.body;
  if (!body || body.dataset.authProtected !== "true") return;

  const navEntries =
    typeof performance !== "undefined" && typeof performance.getEntriesByType === "function"
      ? performance.getEntriesByType("navigation")
      : [];
  const esBackForward = navEntries.length > 0 && navEntries[0].type === "back_forward";

  if (event.persisted || esBackForward) {
    window.location.reload();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-menu-toggle]").forEach((toggle) => {
    const targetId = toggle.getAttribute("aria-controls");
    const menu = targetId ? document.getElementById(targetId) : null;
    if (!menu) return;

    const mediaQuery = window.matchMedia("(max-width: 48rem)");

    const setExpanded = (expanded) => {
      if (!mediaQuery.matches) {
        toggle.setAttribute("aria-expanded", "true");
        menu.hidden = false;
        menu.classList.add("is-open");
        return;
      }
      toggle.setAttribute("aria-expanded", String(expanded));
      menu.hidden = !expanded;
      menu.classList.toggle("is-open", expanded);
    };

    const syncViewport = () => {
      if (mediaQuery.matches) {
        setExpanded(false);
      } else {
        setExpanded(true);
      }
    };

    syncViewport();

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", syncViewport);
    }

    toggle.addEventListener("click", () => {
      if (!mediaQuery.matches) return;
      setExpanded(toggle.getAttribute("aria-expanded") !== "true");
    });

    menu.addEventListener("click", (event) => {
      if (mediaQuery.matches && event.target.closest("a")) {
        setExpanded(false);
      }
    });

    menu.addEventListener("keydown", (event) => {
      if (mediaQuery.matches && event.key === "Escape") {
        setExpanded(false);
        toggle.focus();
      }
    });
  });
});
