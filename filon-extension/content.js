/**
 * FILON — content script
 *
 * Sur une fiche produit d'un marchand supporté, FILON :
 *   1. détecte le produit (JSON-LD Product → OpenGraph → sélecteurs marchand → <h1>) ;
 *   2. affiche une pastille discrète, non intrusive, en bas à droite ;
 *   3. déroule un panneau qui rappelle les données que FILON peut rechercher,
 *      puis emmène l'utilisateur vers l'analyse RÉELLE sur filon.be.
 *
 * Principe : aucune économie chiffrée n'est inventée ici. L'extension ne fait
 * que détecter et relier ; filon.be indique son périmètre et ses inconnues.
 */
(() => {
  "use strict";
  if (window.__FILON_INJECTED__) return;
  window.__FILON_INJECTED__ = true;

  const SITE = "https://filon.be";
  const PREFIX = "filon-x";

  /* ---- détection produit ------------------------------------------------ */

  function fromJsonLd() {
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const data = JSON.parse(s.textContent);
        const items = Array.isArray(data) ? data : [data];
        for (const it of items) {
          const type = it && it["@type"];
          const isProduct = type === "Product" || (Array.isArray(type) && type.includes("Product"));
          if (isProduct && it.name) return String(it.name).trim();
        }
      } catch {
        /* JSON-LD malformé — on ignore */
      }
    }
    return null;
  }

  function fromMerchant() {
    // Sélecteurs de titre spécifiques aux marchands supportés.
    const sels = [
      "#productTitle", // Amazon
      "[data-test='title']", // bol.com / coolblue
      ".js-product-name",
      ".product-title",
      "h1[itemprop='name']",
      ".f-productHeader__title", // Fnac
    ];
    for (const sel of sels) {
      const t = document.querySelector(sel)?.textContent?.trim();
      if (t) return t;
    }
    return null;
  }

  function detectProduct() {
    const og = document.querySelector('meta[property="og:type"]')?.content || "";
    const looksLikeProduct =
      og.includes("product") ||
      document.querySelector('[itemtype*="schema.org/Product"], #productTitle, .f-productHeader__title');
    const name =
      fromJsonLd() ||
      fromMerchant() ||
      (looksLikeProduct ? document.querySelector('meta[property="og:title"]')?.content : null) ||
      (looksLikeProduct ? document.querySelector("h1")?.textContent?.trim() : null);
    if (!name) return null;
    // Nettoyage léger : couper les suffixes marchands après un séparateur.
    const clean = name.split(/[|·–—:]\s/)[0].trim().slice(0, 140);
    return clean.length >= 3 ? { name: clean } : null;
  }

  /* ---- rendu ------------------------------------------------------------ */

  function esc(str) {
    return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  const LOGO = `<svg viewBox="0 0 240 240" width="26" height="26" aria-hidden="true">
    <defs><linearGradient id="${PREFIX}-g" gradientUnits="userSpaceOnUse" x1="95" y1="166" x2="156" y2="78">
      <stop stop-color="#86D1B0"/><stop offset="1" stop-color="#8FB9E6"/></linearGradient></defs>
    <rect x="8" y="8" width="224" height="224" rx="49.28" fill="#26364B"/>
    <g fill="none" stroke="url(#${PREFIX}-g)" stroke-width="17" stroke-linecap="round" stroke-linejoin="round"><path d="M95 78 L95 166"/><path d="M95 78 L156 78"/><path d="M95 121 L145 121"/></g>
    <circle cx="156" cy="78" r="10.5" fill="#EF9F27"/></svg>`;

  const CHECKS = [
    ["Offres indexées", "prix observés pour le produit reconnu"],
    ["Alternative reconditionnée", "lorsqu'une offre comparable existe"],
    ["Promotions disponibles", "lorsqu'une source en fournit les conditions"],
    ["Cashback connu", "affiché seulement lorsqu'il est documenté"],
  ];

  function openFilon(name) {
    const url = `${SITE}/recherche?q=${encodeURIComponent(name)}&utm_source=extension&utm_medium=fiche`;
    window.open(url, "_blank", "noopener");
  }

  function render(product) {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const pill = document.createElement("button");
    pill.className = `${PREFIX}-pill`;
    pill.setAttribute("aria-label", "Ouvrir l'analyse FILON");
    pill.innerHTML = `${LOGO}<span>Vérifier avec FILON</span>`;

    const panel = document.createElement("aside");
    panel.className = `${PREFIX}-panel`;
    panel.setAttribute("role", "complementary");
    panel.setAttribute("aria-label", "FILON — les offres observées");
    panel.innerHTML = `
      <div class="${PREFIX}-head">
        ${LOGO}
        <div class="${PREFIX}-brand">FILON<small>Les offres observées, avant d'acheter</small></div>
        <button class="${PREFIX}-close" aria-label="Fermer">✕</button>
      </div>
      <div class="${PREFIX}-detected">
        <span class="${PREFIX}-dl">Produit repéré</span>
        <b>${esc(product.name)}</b>
      </div>
      <div class="${PREFIX}-checks">
        ${CHECKS.map(
          ([a, b], i) => `
          <div class="${PREFIX}-check" data-i="${i}">
            <span class="${PREFIX}-tick"><svg viewBox="0 0 24 24" width="14" height="14"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
            <div><div class="${PREFIX}-ca">${esc(a)}</div><div class="${PREFIX}-cb">${esc(b)}</div></div>
          </div>`
        ).join("")}
      </div>
      <button class="${PREFIX}-cta">Voir l'analyse sur FILON →</button>
      <div class="${PREFIX}-foot">Accès actuel à 0 € · certains liens sont affiliés · conditions à confirmer chez le marchand.</div>
    `;

    document.body.appendChild(pill);
    document.body.appendChild(panel);

    const checks = panel.querySelectorAll(`.${PREFIX}-check`);
    const revealAll = () => checks.forEach((c) => c.classList.add(`${PREFIX}-on`));

    let open = false;
    const setOpen = (v) => {
      open = v;
      panel.classList.toggle(`${PREFIX}-show`, v);
      pill.classList.toggle(`${PREFIX}-hide`, v);
      if (v) {
        if (reduced) revealAll();
        else checks.forEach((c, i) => setTimeout(() => c.classList.add(`${PREFIX}-on`), 220 + i * 180));
      }
    };

    pill.addEventListener("click", () => setOpen(true));
    panel.querySelector(`.${PREFIX}-close`).addEventListener("click", () => setOpen(false));
    panel.querySelector(`.${PREFIX}-cta`).addEventListener("click", () => openFilon(product.name));

    // Auto-ouverture douce, sauf si l'utilisateur l'a fermé sur ce marchand
    // dans les 12 dernières heures. storage.local est accessible depuis un
    // content script (contrairement à storage.session, réservé au worker).
    const key = `${PREFIX}-dismissed:${location.host}`;
    const autoOpen = () => setTimeout(() => setOpen(true), 900);
    try {
      chrome.storage.local.get(key, (r) => {
        if (chrome.runtime.lastError) return autoOpen();
        const ts = r && r[key];
        if (!ts || Date.now() - ts > 12 * 3600 * 1000) autoOpen();
      });
      panel.querySelector(`.${PREFIX}-close`).addEventListener("click", () => {
        try { chrome.storage.local.set({ [key]: Date.now() }); } catch {}
      });
    } catch {
      autoOpen();
    }
  }

  const product = detectProduct();
  if (product) render(product);
})();
