/* FILON popup — reads saved stats and the on/off toggle from chrome.storage. */
(() => {
  "use strict";
  const euro = (n) => `${Number(n).toLocaleString("fr-FR")} €`;
  const api = typeof chrome !== "undefined" ? chrome : undefined;

  const monthEl = document.getElementById("month");
  const totalEl = document.getElementById("total");
  const countEl = document.getElementById("count");
  const sw = document.getElementById("switch");

  const defaults = { monthSaved: 0, totalSaved: 0, filonCount: 0, active: true };

  function paint(state) {
    monthEl.textContent = euro(state.monthSaved);
    totalEl.textContent = euro(state.totalSaved);
    countEl.textContent = String(state.filonCount);
    sw.setAttribute("aria-pressed", state.active ? "true" : "false");
  }

  if (api?.storage?.local) {
    api.storage.local.get(defaults, paint);
    sw.addEventListener("click", () => {
      const next = sw.getAttribute("aria-pressed") !== "true";
      sw.setAttribute("aria-pressed", next ? "true" : "false");
      api.storage.local.set({ active: next });
    });
  } else {
    // Fallback when opened outside the extension context.
    paint(defaults);
    sw.addEventListener("click", () => {
      const next = sw.getAttribute("aria-pressed") !== "true";
      sw.setAttribute("aria-pressed", next ? "true" : "false");
    });
  }
})();
