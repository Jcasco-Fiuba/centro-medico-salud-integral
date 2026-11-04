// Interacciones compartidas de interfaz. No realizar solicitudes a la API aquí.

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-menu-toggle]").forEach((toggle) => {
    const targetId = toggle.getAttribute("aria-controls");
    const menu = targetId ? document.getElementById(targetId) : null;

    if (!menu) return;

    const setExpanded = (expanded) => {
      toggle.setAttribute("aria-expanded", String(expanded));
      menu.hidden = !expanded;
    };

    setExpanded(toggle.getAttribute("aria-expanded") === "true");

    toggle.addEventListener("click", () => {
      setExpanded(toggle.getAttribute("aria-expanded") !== "true");
    });

    menu.addEventListener("click", (event) => {
      if (event.target.closest("a")) setExpanded(false);
    });

    menu.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        setExpanded(false);
        toggle.focus();
      }
    });
  });
});
