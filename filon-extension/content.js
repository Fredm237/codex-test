/**
 * FILON — content script (prototype)
 *
 * Runs on a product page, detects the product, then injects the FILON overlay
 * that compares cashback / reconditionné / codes promo and reveals the real price.
 *
 * In production, `compareOffers()` would call the FILON API with the detected
 * product; here it returns an illustrative, clearly-simulated result so the
 * prototype is fully self-contained.
 */
(() => {
  "use strict";
  if (window.__FILON_INJECTED__) return;
  window.__FILON_INJECTED__ = true;

  const PREFIX = "filon-x";
  const euro = (n) => `${n.toLocaleString("fr-FR")} €`;

  /** Best-effort product detection: JSON-LD Product → OpenGraph → <h1> + price. */
  function detectProduct() {
    // 1. Schema.org Product via JSON-LD
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const data = JSON.parse(s.textContent);
        const items = Array.isArray(data) ? data : [data];
        for (const it of items) {
          if (it && (it["@type"] === "Product" || (Array.isArray(it["@type"]) && it["@type"].includes("Product")))) {
            const offer = Array.isArray(it.offers) ? it.offers[0] : it.offers;
            const price = offer && (offer.price || offer.lowPrice);
            if (it.name && price) return { name: String(it.name), price: parseFloat(price) };
          }
        }
      } catch {
        /* ignore malformed JSON-LD */
      }
    }
    // 2. OpenGraph title + a price-looking number on the page
    const ogTitle = document.querySelector('meta[property="og:title"]')?.content;
    const priceEl = document.querySelector("[data-price], .price, [itemprop='price']");
    const priceText = priceEl?.getAttribute("content") || priceEl?.textContent || "";
    const priceMatch = priceText.match(/(\d[\d\s.,]*)/);
    const title = ogTitle || document.querySelector("h1")?.textContent?.trim();
    if (title && priceMatch) {
      const price = parseFloat(priceMatch[1].replace(/\s/g, "").replace(",", "."));
      if (price) return { name: title, price };
    }
    return null;
  }

  /**
   * Compute the best cumulative saving. Simulated for the prototype.
   * Returns the sources and the resulting real price.
   */
  function compareOffers(product) {
    const p = product.price;
    const cashbackRate = 6.5; // best of compared cashback platforms
    const recondPrice = Math.round(p * 0.81); // reconditioned equivalent ≈ -19%
    const promo = 15;
    const base = Math.min(p, recondPrice) - promo;
    const cashback = Math.round(base * (cashbackRate / 100));
    const realPrice = Math.max(0, base - cashback);
    return {
      sources: [
        { ic: "i", a: "Cashback — iGraal", b: "le mieux-disant des 42 comparés", v: `+${cashbackRate}`.replace(".", ",") + " %" },
        { ic: "R", a: "Reconditionné A+", b: "garanti 24 mois · Back Market", v: `−${euro(p - recondPrice)}` },
        { ic: "%", a: "Code promo vérifié", b: "testé en direct · valide", v: `−${euro(promo)}` },
        { ic: "€", a: "Prix marchand le plus bas", b: "37 marchands en temps réel", v: euro(recondPrice) },
      ],
      realPrice,
      saving: p - realPrice,
    };
  }

  function el(tag, cls, html) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (html != null) node.innerHTML = html;
    return node;
  }

  const LOGO = `<svg viewBox="0 0 32 32" fill="none" width="26" height="26"><defs><linearGradient id="${PREFIX}-lg" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#3C7BFF"/><stop offset=".5" stop-color="#8B6CFF"/><stop offset="1" stop-color="#24E3C6"/></linearGradient></defs><rect x="1.5" y="1.5" width="29" height="29" rx="9" stroke="url(#${PREFIX}-lg)" stroke-width="2"/><path d="M9 22 L15 9 L18 16 L23 10" stroke="url(#${PREFIX}-lg)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

  function render(product, result) {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const root = el("aside", `${PREFIX}-overlay`);
    root.setAttribute("role", "complementary");
    root.setAttribute("aria-label", "FILON — comparateur d'économies");
    root.innerHTML = `
      <div class="${PREFIX}-head">
        ${LOGO}
        <div class="${PREFIX}-title">FILON<small>Le filon est là.</small></div>
        <button class="${PREFIX}-close" aria-label="Fermer FILON">✕</button>
      </div>
      <div class="${PREFIX}-body">
        <div class="${PREFIX}-scan"><span class="${PREFIX}-spin"></span> Analyse des sources d'économies…</div>
        <div class="${PREFIX}-detected">Produit détecté : <b>${escapeHtml(product.name)}</b></div>
        <div class="${PREFIX}-sources">
          ${result.sources
            .map(
              (s, i) => `
            <div class="${PREFIX}-src" data-i="${i}">
              <span class="${PREFIX}-ic">${s.ic}</span>
              <div class="${PREFIX}-m"><div class="${PREFIX}-a">${escapeHtml(s.a)}</div><div class="${PREFIX}-b">${escapeHtml(s.b)}</div></div>
              <div class="${PREFIX}-v" data-v="${escapeHtml(s.v)}">…</div>
            </div>`
            )
            .join("")}
        </div>
        <div class="${PREFIX}-result">
          <div class="${PREFIX}-rr"><span class="${PREFIX}-lab">Votre prix réel</span><span class="${PREFIX}-amt">${euro(result.realPrice)}</span></div>
          <div class="${PREFIX}-dt">Affiché <b>${euro(product.price)}</b> → économie totale <b class="${PREFIX}-pos">${euro(result.saving)}</b>.</div>
          <button class="${PREFIX}-cta">Appliquer le filon →</button>
        </div>
      </div>
      <div class="${PREFIX}-foot">Lien affilié · FILON perçoit une part de la commission d'apport de la plateforme. Cela n'augmente jamais votre prix. Données non revendues.</div>
    `;
    document.body.appendChild(root);
    requestAnimationFrame(() => root.classList.add(`${PREFIX}-show`));

    const srcs = root.querySelectorAll(`.${PREFIX}-src`);
    const scan = root.querySelector(`.${PREFIX}-scan`);
    const res = root.querySelector(`.${PREFIX}-result`);

    const reveal = (node) => {
      node.classList.add(`${PREFIX}-on`);
      node.querySelector(`.${PREFIX}-v`).textContent = node.querySelector(`.${PREFIX}-v`).getAttribute("data-v");
    };

    if (prefersReduced) {
      srcs.forEach(reveal);
      scan.style.display = "none";
      res.classList.add(`${PREFIX}-show`);
    } else {
      srcs.forEach((s, i) => setTimeout(() => reveal(s), 450 + i * 420));
      setTimeout(() => {
        scan.style.display = "none";
        res.classList.add(`${PREFIX}-show`);
      }, 450 + srcs.length * 420 + 200);
    }

    root.querySelector(`.${PREFIX}-close`).addEventListener("click", () => root.remove());
    root.querySelector(`.${PREFIX}-cta`).addEventListener("click", () => {
      // In production: open the affiliate deep-link for the winning offer.
      window.open("https://filon.app/redirect?demo=1", "_blank", "noopener");
    });
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  const product = detectProduct();
  if (product) {
    render(product, compareOffers(product));
  }
})();
