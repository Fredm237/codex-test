/* FILON — service worker (MV3).
 *
 * Minimal et honnête : à l'installation, on ouvre la page d'accueil FILON pour
 * expliquer l'extension. Aucun suivi, aucune donnée collectée en arrière-plan.
 * La résolution des liens affiliés se fera côté FILON, sur des données réelles.
 */
const SITE = "https://filon.be";

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    chrome.tabs.create({ url: `${SITE}/?utm_source=extension&utm_medium=install` });
  }
});
