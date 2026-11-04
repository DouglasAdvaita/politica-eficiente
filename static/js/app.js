/* Detalles de interacción: sin frameworks. */
document.addEventListener("DOMContentLoaded", () => {
  // Marcar el enlace activo del menú.
  const ruta = location.pathname;
  document.querySelectorAll(".barra nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href && href !== "/" && ruta.startsWith(href)) a.classList.add("activo");
  });

  // Resaltar un tipo de línea del mapa al pasar por encima.
  const svg = document.querySelector(".mapa-svg");
  if (svg) {
    svg.querySelectorAll(".nodo").forEach((nodo) => {
      nodo.addEventListener("mouseenter", () => {
        svg.classList.remove("destacar-politicos", "destacar-usuarios");
        if (nodo.classList.contains("politico")) svg.classList.add("destacar-politicos");
        if (nodo.classList.contains("grupo")) svg.classList.add("destacar-usuarios");
      });
      nodo.addEventListener("mouseleave", () => {
        svg.classList.remove("destacar-politicos", "destacar-usuarios");
      });
    });
  }

  // Textarea que crece y contador simple.
  document.querySelectorAll("textarea").forEach((t) => {
    t.addEventListener("input", () => {
      t.style.height = "auto";
      t.style.height = Math.min(t.scrollHeight, 320) + "px";
    });
  });

  // Confirmación en acciones destructivas o delicadas.
  document.querySelectorAll("form[data-confirmar]").forEach((f) => {
    f.addEventListener("submit", (e) => {
      if (!confirm(f.dataset.confirmar)) e.preventDefault();
    });
  });
});
