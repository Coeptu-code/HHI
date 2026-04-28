// MVP scaffold (Black Dashboard-ready: add UI behavior later)
(() => {
  function handleCopyClick(event) {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("copy-btn")) return;

    const text = target.getAttribute("data-copy") || "";
    if (!text) return;

    const setCopied = (ok) => {
      const original = target.textContent || "Copy";
      target.textContent = ok ? "Copied" : "Copy failed";
      setTimeout(() => {
        target.textContent = original;
      }, 1200);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(text)
        .then(() => setCopied(true))
        .catch(() => {
          window.prompt("Copy this link:", text);
          setCopied(true);
        });
      return;
    }

    window.prompt("Copy this link:", text);
    setCopied(true);
  }

  document.addEventListener("click", handleCopyClick);
})();
