(() => {
  function enhanceChoiceGroups() {
    const groups = document.querySelectorAll(".choice-group");
    groups.forEach((group) => {
      const radios = group.querySelectorAll("input[type='radio']");
      if (!radios.length) return;

      const update = () => {
        const labels = group.querySelectorAll("label");
        labels.forEach((label) => label.classList.remove("is-selected"));
        radios.forEach((radio) => {
          if (!(radio instanceof HTMLInputElement)) return;
          if (!radio.checked) return;
          const label = radio.closest("label");
          if (label) label.classList.add("is-selected");
        });
      };

      radios.forEach((radio) => {
        radio.addEventListener("change", update);
      });
      update();
    });
  }

  function focusFirstInput() {
    const root = document.querySelector("[data-intake-autofocus]");
    if (!root) return;
    const candidate = root.querySelector(
      "input:not([type='hidden']):not([disabled]), select:not([disabled]), textarea:not([disabled])",
    );
    if (!(candidate instanceof HTMLElement)) return;
    if (candidate.matches("input[type='radio'], input[type='checkbox']")) return;
    candidate.focus({ preventScroll: true });
  }

  document.addEventListener("DOMContentLoaded", () => {
    enhanceChoiceGroups();
    focusFirstInput();
  });
})();

