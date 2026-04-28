(function () {
  const roots = document.querySelectorAll(".drug-search-root");
  if (!roots.length) {
    return;
  }

  function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
      if (timer) {
        window.clearTimeout(timer);
      }
      timer = window.setTimeout(() => fn.apply(this, args), delay);
    };
  }

  roots.forEach((root) => {
    const searchUrl = root.getAttribute("data-search-url");
    const input = root.querySelector("input[name='drug_search']");
    const resultsBox = root.querySelector("[data-search-results]");
    const idField = root.querySelector("input[name='selected_drug_id']");
    const nameField = root.querySelector("input[name='selected_drug_name']");
    const normalizedField = root.querySelector("input[name='normalized_drug_name']");
    const sourceField = root.querySelector("input[name='source']");

    if (!searchUrl || !input || !resultsBox || !idField || !nameField || !normalizedField || !sourceField) {
      return;
    }

    const renderResults = (items) => {
      resultsBox.innerHTML = "";
      if (!items.length) {
        resultsBox.hidden = true;
        return;
      }

      items.forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = item.display_name;
        button.addEventListener("click", () => {
          input.value = item.display_name;
          idField.value = item.id || "";
          nameField.value = item.name || item.display_name || "";
          normalizedField.value = item.display_name || item.name || "";
          sourceField.value = "rxterms";
          resultsBox.hidden = true;
        });
        resultsBox.appendChild(button);
      });
      resultsBox.hidden = false;
    };

    const doSearch = debounce(async () => {
      const query = input.value.trim();
      if (query.length < 2) {
        resultsBox.hidden = true;
        return;
      }

      idField.value = "";
      nameField.value = "";
      normalizedField.value = "";
      sourceField.value = "manual";

      try {
        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          renderResults([]);
          return;
        }
        const items = await response.json();
        renderResults(Array.isArray(items) ? items : []);
      } catch (_error) {
        renderResults([]);
      }
    }, 250);

    input.addEventListener("input", doSearch);
  });
})();
