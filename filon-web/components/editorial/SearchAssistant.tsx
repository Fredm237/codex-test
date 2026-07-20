"use client";

import { useRef, useState } from "react";

/* ────────────────────────────────────────────────────────────────────────
   PRODUCT MODE — deep single-product analysis (best neuf / recond / cashback)
   ──────────────────────────────────────────────────────────────────────── */
type Deal = { offers: number; newP: number; merchant: string; recP: number; recPct: number; cb: number; cbP: string; advise: string; real: number };

const DB: Record<string, Deal> = {
  "iphone 18 pro": { offers: 42, newP: 1199, merchant: "Amazon", recP: 985, recPct: 18, cb: 5.5, cbP: "Widilo", advise: "attendez six jours, le prix baisse souvent avant le week-end", real: 930 },
  ps6: { offers: 37, newP: 599, merchant: "Fnac", recP: 519, recPct: 13, cb: 4, cbP: "iGraal", advise: "achetez maintenant, le stock est tendu et aucune baisse ne se profile avant les fêtes", real: 498 },
  "dyson v15": { offers: 34, newP: 549, merchant: "Boulanger", recP: 379, recPct: 31, cb: 6.5, cbP: "Poulpeo", advise: "le reconditionné grade A+ est la meilleure affaire ce mois-ci", real: 354 },
  "airpods pro": { offers: 29, newP: 279, merchant: "Amazon", recP: 229, recPct: 18, cb: 5, cbP: "Widilo", advise: "un code promo valide fait tomber le neuf sous le reconditionné aujourd'hui", real: 214 },
  "macbook air": { offers: 31, newP: 1299, merchant: "Amazon", recP: 1049, recPct: 19, cb: 4.5, cbP: "eBuyClub", advise: "attendez la rentrée, une remise étudiante est probable sous dix jours", real: 1002 },
};

function synthDeal(q: string): Deal {
  let seed = 0;
  for (let i = 0; i < q.length; i++) seed = (seed * 31 + q.charCodeAt(i)) >>> 0;
  const newP = 120 + (seed % 900);
  const recPct = 12 + (seed % 24);
  const recP = Math.round(newP * (1 - recPct / 100));
  const cb = 4 + (seed % 5);
  const real = Math.max(20, Math.round(recP * (1 - cb / 100)) - (seed % 15));
  const merchants = ["Amazon", "Fnac", "Cdiscount", "Boulanger", "Darty"];
  const cbs = ["iGraal", "Poulpeo", "Widilo", "Joko", "eBuyClub"];
  const advs = [
    "attendez quelques jours, une baisse est probable avant le week-end",
    "achetez maintenant, c'est le meilleur prix vu en 90 jours",
    "le reconditionné équivalent est la meilleure affaire ce mois-ci",
  ];
  return { offers: 20 + (seed % 30), newP, merchant: merchants[seed % 5], recP, recPct, cb, cbP: cbs[(seed >> 3) % 5], advise: advs[seed % 3], real };
}

/* ────────────────────────────────────────────────────────────────────────
   NEED MODE — describe a need + budget → 3 recommendations + buy/wait verdict
   ──────────────────────────────────────────────────────────────────────── */
type Pick = { name: string; rank: string; fit: string; price: number; merchant: string; now: number; avg6: number; low: number; buy: boolean; best?: boolean };
type Need = { usage: string; priorities: string; picks: Pick[]; verdict: string };

const NEEDS: { keys: RegExp; budget: number; build: (b: number) => Need }[] = [
  {
    keys: /montage|vidéo|video|monteur|rush|premiere|davinci|youtube/,
    budget: 1200,
    build: (b) => ({
      usage: "Montage vidéo",
      priorities: "CPU/GPU, écran calibré, RAM 32 Go",
      verdict: "Acheter maintenant. Le prix est proche du plancher, aucune baisse attendue avant 30 jours.",
      picks: [
        { name: "ASUS ProArt Studiobook", rank: "Le plus taillé pour la vidéo", fit: "Écran 4K OLED calibré usine, GPU RTX pour l'export, 32 Go RAM. La machine de monteur.", price: 1189, merchant: "LDLC", now: 1189, avg6: 1349, low: 1149, buy: true, best: true },
        { name: "MacBook Air (puce M)", rank: "Meilleure autonomie / silence", fit: "Silencieux, ~18 h d'autonomie, export 1080p fluide. Parfait en mobilité.", price: 1049, merchant: "Amazon", now: 1049, avg6: 1129, low: 999, buy: true },
        { name: "Lenovo Legion · reconditionné A+", rank: "Le plus d'économie", fit: "GPU dédié, garanti 24 mois, −32 % vs neuf. Le meilleur euro/perf.", price: 899, merchant: "Back Market", now: 899, avg6: 999, low: 879, buy: false },
      ],
    }),
  },
  {
    keys: /gaming|gamer|jeux?|jouer|fps|esport|pc de jeu/,
    budget: 1000,
    build: (b) => ({
      usage: "Gaming",
      priorities: "GPU, taux de rafraîchissement, refroidissement",
      verdict: "Acheter maintenant. Le modèle vedette est à son meilleur prix depuis 90 jours.",
      picks: [
        { name: "MSI Katana · RTX", rank: "Le meilleur rapport perf/prix", fit: "GPU RTX, écran 144 Hz, refroidissement sérieux. Tourne tout en 1080p élevé.", price: 999, merchant: "Cdiscount", now: 999, avg6: 1149, low: 979, buy: true, best: true },
        { name: "Lenovo LOQ", rank: "L'entrée de gamme maligne", fit: "Bon GPU, châssis solide, silencieux. Idéal pour débuter sans exploser le budget.", price: 849, merchant: "Fnac", now: 849, avg6: 899, low: 829, buy: true },
        { name: "PC fixe reconditionné A+", rank: "Le plus évolutif", fit: "Plus puissant à budget égal, garanti 24 mois, évolutif. Si la mobilité n'est pas clé.", price: 780, merchant: "Back Market", now: 780, avg6: 860, low: 770, buy: false },
      ],
    }),
  },
  {
    keys: /smartphone|téléphone|telephone|\btel\b|portable android|pixel|galaxy|iphone/,
    budget: 500,
    build: (b) => ({
      usage: "Smartphone",
      priorities: "Photo, autonomie, longévité des mises à jour",
      verdict: "Attendre une semaine. Une promotion récurrente fait souvent baisser ce modèle d'environ 40 €.",
      picks: [
        { name: "Google Pixel (série a)", rank: "La meilleure photo à ce prix", fit: "Photo de référence, Android pur, 7 ans de mises à jour. Le plus pérenne.", price: 499, merchant: "Amazon", now: 499, avg6: 549, low: 459, buy: false, best: true },
        { name: "Samsung Galaxy A · 5G", rank: "Le meilleur écran / autonomie", fit: "Grand écran AMOLED, grosse batterie, très bonne autonomie. Polyvalent.", price: 379, merchant: "Boulanger", now: 379, avg6: 429, low: 369, buy: true },
        { name: "iPhone · reconditionné A+", rank: "Le plus d'économie sur iOS", fit: "Un iPhone récent garanti 24 mois, −30 % vs neuf. Pour rester sur iOS malin.", price: 449, merchant: "Back Market", now: 449, avg6: 499, low: 439, buy: true },
      ],
    }),
  },
  {
    keys: /casque|écouteurs|ecouteurs|audio|son|sport/,
    budget: 200,
    build: (b) => ({
      usage: "Audio / casque",
      priorities: "Réduction de bruit, autonomie, confort",
      verdict: "Acheter maintenant. Le reconditionné grade A+ passe sous le neuf sur ce modèle aujourd'hui.",
      picks: [
        { name: "Sony WH · réduction de bruit", rank: "La meilleure réduction de bruit", fit: "Référence anti-bruit, 30 h d'autonomie, très confortable. Le haut du panier.", price: 279, merchant: "Fnac", now: 279, avg6: 329, low: 259, buy: false, best: true },
        { name: "Écouteurs sport étanches", rank: "Le meilleur pour le sport", fit: "Maintien parfait, étanches, autonomie généreuse. Pensés pour bouger.", price: 129, merchant: "Amazon", now: 129, avg6: 149, low: 119, buy: true },
        { name: "Casque reconditionné A+", rank: "Le plus d'économie", fit: "Le même modèle premium, garanti 24 mois, −35 % vs neuf.", price: 189, merchant: "Back Market", now: 189, avg6: 219, low: 179, buy: true },
      ],
    }),
  },
];

function synthNeed(q: string, budget: number | null): Need {
  let seed = 0;
  for (let i = 0; i < q.length; i++) seed = (seed * 31 + q.charCodeAt(i)) >>> 0;
  const base = budget || 200 + (seed % 800);
  const merchants = ["Amazon", "Fnac", "Cdiscount", "Boulanger", "Darty"];
  const mk = (mult: number, i: number, rank: string, fit: string, buy: boolean, best?: boolean): Pick => {
    const now = Math.round(base * mult);
    return { name: `Option ${i + 1}`, rank, fit, price: now, merchant: merchants[(seed >> i) % 5], now, avg6: Math.round(now * 1.12), low: Math.round(now * 0.96), buy, best };
  };
  return {
    usage: q.trim().replace(/^\w/, (c) => c.toUpperCase()),
    priorities: "rapport qualité/prix, fiabilité, garantie",
    verdict: "Acheter maintenant. La sélection est au meilleur prix vu récemment.",
    picks: [
      mk(0.98, 0, "Le meilleur choix global", "Le meilleur équilibre performances, fiabilité et prix pour votre besoin.", true, true),
      mk(0.82, 1, "Le plus économique", "Presque aussi bon, sensiblement moins cher. Le choix malin.", true),
      mk(0.7, 2, "Reconditionné A+", "L'équivalent reconditionné, garanti 24 mois. Le maximum d'économie.", false),
    ],
  };
}

/* ── shared helpers ── */
const euro = (n: number) => `${n.toLocaleString("fr-FR")} €`;

function detectNeed(q: string): { need: Need; budget: number | null } | null {
  const s = q.toLowerCase();
  const bm = s.replace(/\s/g, "").match(/(\d{2,5})(?:€|eur)/i) || s.match(/(?:budget|à|a|vers|max|autour|environ)\D{0,6}(\d{2,5})/i);
  const budget = bm ? parseInt(bm[1], 10) : null;
  const looksLikeNeed = budget != null || /\bpour\b|montage|gaming|jouer|jeux|photo|bureautique|étudiant|travail|voyage|cadeau|débuter|sport|besoin/.test(s);
  if (!looksLikeNeed) return null;
  const hit = NEEDS.find((n) => n.keys.test(s));
  if (hit) return { need: hit.build(budget || hit.budget), budget: budget || hit.budget };
  // need-shaped but unknown category → synthesize
  if (budget != null || s.split(/\s+/).length >= 4) return { need: synthNeed(q, budget), budget };
  return null;
}

const CHIPS = ["PC pour montage vidéo, 1200€", "Un bon smartphone à 500€", "PC gaming ~1000€", "iPhone 18 Pro"];

export function SearchAssistant() {
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [mode, setMode] = useState<"need" | "product">("product");
  const answerRef = useRef<HTMLDivElement>(null);
  const timers = useRef<number[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => clearTimeout(t));
    timers.current = [];
  };

  /* ── PRODUCT-MODE renderer (unchanged flow) ── */
  const buildProduct = (name: string, d: Deal) => {
    const el = answerRef.current;
    if (!el) return;
    const text = el.querySelector(".sa-text") as HTMLElement;
    const results = el.querySelector(".sa-results") as HTMLElement;
    const verdict = el.querySelector(".sa-verdict") as HTMLElement;
    const vp = el.querySelector(".sa-vp") as HTMLElement;
    const vs = el.querySelector(".sa-vs") as HTMLElement;
    const cnt = el.querySelector(".sa-cnt") as HTMLElement;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    cnt.textContent = `${d.offers} offres`;
    const segs: { t: string; c?: string }[] = [
      { t: "J'ai analysé " }, { t: `${d.offers} offres`, c: "ent" }, { t: " pour " }, { t: name, c: "ent" },
      { t: ". Le meilleur prix neuf est chez " }, { t: d.merchant, c: "ent" }, { t: " à " }, { t: euro(d.newP), c: "ent" },
      { t: ". En reconditionné grade A+, on descend à " }, { t: euro(d.recP), c: "save" }, { t: ", soit " },
      { t: `−${d.recPct} %`, c: "save" }, { t: ", garanti 24 mois. Le cashback le plus élevé est chez " }, { t: d.cbP, c: "ent" },
      { t: " (" }, { t: `${d.cb.toString().replace(".", ",")} %`, c: "save" }, { t: ")." },
    ];
    text.innerHTML = "";
    const words: HTMLElement[] = [];
    segs.forEach((s) => {
      s.t.split(/(\s+)/).forEach((tok) => {
        if (tok === "") return;
        if (/^\s+$/.test(tok)) { text.appendChild(document.createTextNode(tok)); return; }
        const sp = document.createElement("span");
        sp.className = "w" + (s.c ? " " + s.c : "");
        sp.textContent = tok;
        text.appendChild(sp);
        words.push(sp);
      });
    });
    const tip = document.createElement("span");
    tip.className = "sa-tip";
    tip.innerHTML = `💡 <b>Mon conseil :</b> ${d.advise}.`;
    tip.style.opacity = "0";
    tip.style.transition = "opacity .5s var(--ease-out)";
    text.appendChild(tip);

    const cards = [
      { lab: "Meilleur prix neuf", val: euro(d.newP), g: false, sub: `${d.merchant} · livraison incluse`, tag: "" },
      { lab: "Reconditionné A+", val: euro(d.recP), g: true, sub: "garanti 24 mois · Back Market", tag: `−${d.recPct} %` },
      { lab: "Meilleur cashback", val: `${d.cb.toString().replace(".", ",")} %`, g: true, sub: `appliqué via ${d.cbP}`, tag: "" },
    ];
    results.innerHTML = cards
      .map((c) => `<div class="sa-r"><div class="lab">${c.lab}</div><div class="val${c.g ? " g" : ""}">${c.val}</div><div class="sub">${c.sub}</div>${c.tag ? `<span class="tag">${c.tag}</span>` : ""}</div>`)
      .join("");
    const rEls = Array.from(results.querySelectorAll(".sa-r")) as HTMLElement[];

    const saved = d.newP - d.real;
    const pct = Math.round((saved / d.newP) * 100);

    const finish = () => {
      rEls.forEach((r, i) => timers.current.push(window.setTimeout(() => r.classList.add("in"), reduce ? 0 : i * 90)));
      timers.current.push(
        window.setTimeout(() => {
          verdict.classList.add("in");
          vs.textContent = `vous économisez ${euro(saved)} · −${pct} %`;
          if (reduce) { vp.textContent = euro(d.real); return; }
          const s = performance.now();
          const tick = (n: number) => {
            const p = Math.min((n - s) / 900, 1);
            const e = 1 - Math.pow(1 - p, 3);
            vp.textContent = euro(Math.round(d.real * e));
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }, reduce ? 0 : rEls.length * 90 + 200)
      );
    };

    if (reduce) {
      words.forEach((w) => w.classList.add("show"));
      tip.style.opacity = "1";
      finish();
    } else {
      words.forEach((w, i) => timers.current.push(window.setTimeout(() => w.classList.add("show"), i * 26)));
      const done = words.length * 26 + 250;
      timers.current.push(window.setTimeout(() => (tip.style.opacity = "1"), done));
      timers.current.push(window.setTimeout(finish, done + 300));
    }
  };

  /* ── NEED-MODE renderer ── */
  const buildNeed = (raw: string, need: Need, budget: number | null) => {
    const el = answerRef.current;
    if (!el) return;
    const text = el.querySelector(".sa-text") as HTMLElement;
    const needs = el.querySelector(".sa-needs") as HTMLElement;
    const picksWrap = el.querySelector(".sa-picks") as HTMLElement;
    const verdict = el.querySelector(".sa-verdict") as HTMLElement;
    const vp = el.querySelector(".sa-vp") as HTMLElement;
    const vs = el.querySelector(".sa-vs") as HTMLElement;
    const cnt = el.querySelector(".sa-cnt") as HTMLElement;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const best = need.picks.find((p) => p.best) || need.picks[0];
    cnt.textContent = `${need.picks.length} recommandations`;

    // needs chips
    needs.innerHTML =
      `<span class="sa-need"><span class="k">Usage</span> <b>${need.usage}</b></span>` +
      (budget ? `<span class="sa-need"><span class="k">Budget</span> <b>≈ ${euro(budget)}</b></span>` : "") +
      `<span class="sa-need"><span class="k">Priorités</span> <b>${need.priorities}</b></span>`;

    // analysis sentence (typed)
    const segs: { t: string; c?: string }[] = [
      { t: "J'ai compris votre besoin : " }, { t: need.usage.toLowerCase(), c: "ent" },
      budget ? { t: `, budget ≈ ${euro(budget)}` } : { t: "" },
      { t: `. J'ai comparé le marché et retenu ${need.picks.length} choix, du meilleur global au plus économique.` },
    ];
    text.innerHTML = "";
    const words: HTMLElement[] = [];
    segs.forEach((s) => {
      if (!s.t) return;
      s.t.split(/(\s+)/).forEach((tok) => {
        if (tok === "") return;
        if (/^\s+$/.test(tok)) { text.appendChild(document.createTextNode(tok)); return; }
        const sp = document.createElement("span");
        sp.className = "w" + (s.c ? " " + s.c : "");
        sp.textContent = tok;
        text.appendChild(sp);
        words.push(sp);
      });
    });

    // pick cards
    picksWrap.innerHTML = need.picks
      .map(
        (p) => `
      <div class="sa-pick${p.best ? " best" : ""}">
        <div class="rank">${p.rank}</div>
        <div class="nm">${p.name}</div>
        <div class="fit">${p.fit}</div>
        <div class="pr">${euro(p.price)}</div>
        <div class="mc">meilleur prix réel · ${p.merchant}</div>
        <div class="hist">Actuel <b>${euro(p.now)}</b> · moy. 6 mois ${euro(p.avg6)} · plancher ${euro(p.low)}</div>
        <div class="buy ${p.buy ? "now" : "wait"}">${p.buy ? "✓ Acheter maintenant" : "◷ Mieux vaut attendre"}</div>
      </div>`
      )
      .join("");
    const pEls = Array.from(picksWrap.querySelectorAll(".sa-pick")) as HTMLElement[];

    const finish = () => {
      pEls.forEach((p, i) => timers.current.push(window.setTimeout(() => p.classList.add("in"), reduce ? 0 : i * 120)));
      timers.current.push(
        window.setTimeout(() => {
          verdict.classList.add("in");
          vp.textContent = euro(best.price);
          vs.innerHTML = `<b>${best.name}</b>. ${need.verdict}`;
        }, reduce ? 0 : pEls.length * 120 + 250)
      );
    };

    if (reduce) {
      words.forEach((w) => w.classList.add("show"));
      finish();
    } else {
      words.forEach((w, i) => timers.current.push(window.setTimeout(() => w.classList.add("show"), i * 24)));
      timers.current.push(window.setTimeout(finish, words.length * 24 + 300));
    }
  };

  const ask = (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    clearTimers();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const detected = detectNeed(q);
    const nextMode = detected ? "need" : "product";
    setMode(nextMode);
    setSearched(true);
    setThinking(true);
    const run = () => {
      setThinking(false);
      requestAnimationFrame(() => {
        if (detected) buildNeed(q, detected.need, detected.budget);
        else buildProduct(q, DB[q.toLowerCase()] || synthDeal(q));
      });
    };
    if (reduce) run();
    else timers.current.push(window.setTimeout(run, 1500));
  };

  return (
    <section className={`sa ${searched ? "searched" : ""}`}>
      <div className="ed-wrap">
        {!searched && <span className="eyebrow">Copilote d&apos;achat · IA</span>}
        <h1>{searched ? "Un autre achat à décider ?" : "Que voulez-vous acheter, ou décider ?"}</h1>

        <form
          className="sa-search"
          onSubmit={(e) => {
            e.preventDefault();
            ask(query || "PC pour montage vidéo, 1200€");
          }}
        >
          <div className="sa-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.2-4.2" strokeLinecap="round" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Décrivez un besoin (« PC pour montage vidéo, 1200€ ») ou un produit…"
              aria-label="Décrivez un besoin ou un produit"
              autoComplete="off"
            />
            <button type="submit" className="ed-btn wave">Demander</button>
          </div>
          <div className="sa-chips">
            {CHIPS.map((c) => (
              <button key={c} type="button" className="sa-chip" onClick={() => { setQuery(c); ask(c); }}>
                {c}
              </button>
            ))}
          </div>
        </form>

        <div className={`sa-answer ${searched ? "on" : ""}`} ref={answerRef} aria-live="polite">
          {thinking && (
            <div className="sa-think">
              <span className="sa-orb" /> FILON analyse le marché…
            </div>
          )}
          {!thinking && searched && (
            <>
              <div className="sa-card">
                <div className="sa-head">
                  <span className="sa-dot" /> <b>FILON</b> · {mode === "need" ? "recommandation d'achat" : "conseil d'achat"} <span className="cnt sa-cnt" />
                </div>
                <p className="sa-text" />
                {mode === "need" && <div className="sa-needs" style={{ padding: "0 22px 20px" }} />}
              </div>

              {mode === "need" ? <div className="sa-picks" /> : <div className="sa-results" />}

              <div className="sa-verdict">
                <div>
                  <div className="lab">{mode === "need" ? "Ma recommandation" : "Votre prix réel le plus bas"}</div>
                  <div className="price mono sa-vp">…</div>
                </div>
                <div className="sv sa-vs" />
                <a className="ed-btn wave" href="/#installer">{mode === "need" ? "Voir cette offre" : "Voir l'offre"}</a>
              </div>
              <p className="sa-disc">
                Lien affilié · FILON perçoit une part de la commission d&apos;apport de la plateforme. Cela n&apos;augmente jamais votre prix. Données non revendues.
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
