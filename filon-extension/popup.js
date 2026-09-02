"use strict";

const SITE = "https://filon.be";

function openSearch(query) {
  const q = (query || "").trim();
  const url = q
    ? `${SITE}/recherche?q=${encodeURIComponent(q)}&utm_source=extension&utm_medium=popup`
    : `${SITE}/recherche?utm_source=extension&utm_medium=popup`;
  chrome.tabs.create({ url });
  window.close();
}

function openObservation(observation) {
  const gtin = observation?.page?.gtin;
  if (typeof gtin === "string" && /^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$/.test(gtin)) {
    chrome.tabs.create({
      url: `${SITE}/produits/${encodeURIComponent(gtin)}?utm_source=extension&utm_medium=popup`,
    });
    window.close();
    return;
  }
  openSearch(observation?.page?.title || "");
}

document.getElementById("ask").addEventListener("submit", (e) => {
  e.preventDefault();
  openSearch(document.getElementById("q").value);
});

// « Analyser la page ouverte » : on repart du titre de l'onglet actif comme requête.
document.getElementById("analyze").addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs && tabs[0];
    if (!tab?.id) return openSearch("");
    chrome.tabs.sendMessage(tab.id, { type: "FILON_GET_PRODUCT_OBSERVATION" }, (response) => {
      if (!chrome.runtime.lastError && response?.observation) {
        openObservation(response.observation);
        return;
      }
      let seed = tab.title || "";
      seed = seed.split(/[|·–—:]\s/)[0].trim().slice(0, 140);
      openSearch(seed);
    });
  });
});
