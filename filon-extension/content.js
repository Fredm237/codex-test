/**
 * FILON — content script
 *
 * Sur une fiche produit d'un marchand supporté, FILON :
 *   1. détecte le produit (JSON-LD Product → OpenGraph → sélecteurs marchand → <h1>) ;
 *   2. affiche une pastille discrète, non intrusive, en bas à droite ;
 *   3. déroule un panneau qui rappelle les 4 leviers d'économie que FILON vérifie,
 *      puis emmène l'utilisateur vers l'analyse RÉELLE sur filon.be.
 *
 * Principe : aucune économie chiffrée n'est inventée ici. Le vrai prix est calculé
 * côté FILON, sur des données réelles. L'extension ne fait que détecter et relier.
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

  const LOGO = `<svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
    <defs><linearGradient id="${PREFIX}-g" x1="0" y1="0" x2="40" y2="40">
      <stop stop-color="#18beb0"/><stop offset="1" stop-color="#1e75c9"/></linearGradient></defs>
    <rect x="1.5" y="1.5" width="37" height="37" rx="11" fill="url(#${PREFIX}-g)"/>
    <path d="M14 11h13v3.4H17.4v6.1h8v3.4h-8V29H14z" fill="#fff"/></svg>`;

  const CHECKS = [
    ["Meilleur marchand", "des dizaines de vendeurs comparés en direct"],
    ["Reconditionné certifié", "l'équivalent garanti, quand il existe"],
    ["Code promo vérifié", "testé au paiement, pas de code mort"],
    ["Cashback maximal", "la meilleure plateforme, réunie au prix"],
  ];

  function openFilon(name) {
    const url = `${SITE}/recherche?q=${encodeURIComponent(name)}&utm_source=extension&utm_medium=fiche`;
    window.open(url, "_blank", "noopener");
  }

  function render(product) {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const pill = document.createElement("button");
    pill.className = `${PREFIX}-pill`;
    pill.setAttribute("aria-label", "Ouvrir FILON — voir le vrai prix");
    pill.innerHTML = `${LOGO}<span>Voir le vrai prix</span>`;

    const panel = document.createElement("aside");
    panel.className = `${PREFIX}-panel`;
    panel.setAttribute("role", "complementary");
    panel.setAttribute("aria-label", "FILON — le vrai prix");
    panel.innerHTML = `
      <div class="${PREFIX}-head">
        ${LOGO}
        <div class="${PREFIX}-brand">FILON<small>Le vrai prix, avant d'acheter</small></div>
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
      <button class="${PREFIX}-cta">Voir le vrai prix sur FILON →</button>
      <div class="${PREFIX}-foot">Gratuit · indépendant · vos données ne sont jamais revendues.</div>
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
