(function () {
  function findPasswordInput(button) {
    var targetId = button.getAttribute("data-password-target");
    if (targetId) {
      return document.getElementById(targetId);
    }

    var container = button.closest(".auth-field-control, .documentacion-user-password-wrap, .password-field");
    if (!container) {
      container = button.parentElement;
    }
    return container ? container.querySelector('input[type="password"], input[type="text"]') : null;
  }

  function setVisible(button, input, visible) {
    input.type = visible ? "text" : "password";
    button.classList.toggle("is-active", visible);
    button.setAttribute("aria-pressed", visible ? "true" : "false");
    button.setAttribute("aria-label", visible ? "Ocultar contrasena" : "Ver contrasena");
    button.textContent = visible ? "Ocultar" : "Ver";
  }

  function initPasswordToggles() {
    var buttons = document.querySelectorAll("[data-password-toggle]");

    buttons.forEach(function (button) {
      var input = findPasswordInput(button);
      if (!input) {
        return;
      }

      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () {
        setVisible(button, input, input.type === "password");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPasswordToggles);
  } else {
    initPasswordToggles();
  }
})();
