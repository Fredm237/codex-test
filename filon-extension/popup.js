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

document.getElementById("ask").addEventListener("submit", (e) => {
  e.preventDefault();
  openSearch(document.getElementById("q").value);
});

// « Analyser la page ouverte » : on repart du titre de l'onglet actif comme requête.
document.getElementById("analyze").addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs && tabs[0];
    let seed = tab && tab.title ? tab.title : "";
    // On nettoie les suffixes marchands courants pour ne garder que le produit.
    seed = seed.split(/[|·–—:]\s/)[0].trim().slice(0, 140);
    openSearch(seed);
  });
});
