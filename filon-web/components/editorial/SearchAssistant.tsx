"use client";

import { useRef, useState } from "react";

type Deal = { offers: number; newP: number; merchant: string; recP: number; recPct: number; cb: number; cbP: string; advise: string; real: number };

const DB: Record<string, Deal> = {
  "iphone 18 pro": { offers: 42, newP: 1199, merchant: "Amazon", recP: 985, recPct: 18, cb: 5.5, cbP: "Widilo", advise: "attendez 6 jours — le prix baisse généralement avant le week-end", real: 930 },
  ps6: { offers: 37, newP: 599, merchant: "Fnac", recP: 519, recPct: 13, cb: 4, cbP: "iGraal", advise: "achetez maintenant — le stock est tendu et aucune baisse n'est prévue avant les fêtes", real: 498 },
  "dyson v15": { offers: 34, newP: 549, merchant: "Boulanger", recP: 379, recPct: 31, cb: 6.5, cbP: "Poulpeo", advise: "le reconditionné grade A+ est la meilleure affaire ce mois-ci", real: 354 },
  "airpods pro": { offers: 29, newP: 279, merchant: "Amazon", recP: 229, recPct: 18, cb: 5, cbP: "Widilo", advise: "un code promo valide fait tomber le neuf sous le reconditionné aujourd'hui", real: 214 },
  "macbook air": { offers: 31, newP: 1299, merchant: "Amazon", recP: 1049, recPct: 19, cb: 4.5, cbP: "eBuyClub", advise: "attendez la rentrée — une remise étudiante est probable sous 10 jours", real: 1002 },
};
const CHIPS = ["iPhone 18 Pro", "PS6", "Dyson V15", "MacBook Air"];

function synth(q: string): Deal {
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
    "attendez quelques jours — une baisse est probable avant le week-end",
    "achetez maintenant — c'est le meilleur prix observé sur 90 jours",
    "le reconditionné équivalent est la meilleure affaire ce mois-ci",
  ];
  return { offers: 20 + (seed % 30), newP, merchant: merchants[seed % 5], recP, recPct, cb, cbP: cbs[(seed >> 3) % 5], advise: advs[seed % 3], real };
}
const euro = (n: number) => `${n.toLocaleString("fr-FR")} €`;

export function SearchAssistant() {
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const [thinking, setThinking] = useState(false);
  const answerRef = useRef<HTMLDivElement>(null);
  const timers = useRef<number[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => clearTimeout(t));
    timers.current = [];
  };

  const buildAnswer = (name: string, d: Deal) => {
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
      { t: ". En reconditionné grade A+, on descend à " }, { t: euro(d.recP), c: "save" }, { t: " — soit " },
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

  const ask = (raw: string) => {
    const name = raw.trim();
    if (!name) return;
    clearTimers();
    setSearched(true);
    setThinking(true);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const d = DB[name.toLowerCase()] || synth(name);
    const run = () => {
      setThinking(false);
      requestAnimationFrame(() => buildAnswer(name, d));
    };
    if (reduce) run();
    else timers.current.push(window.setTimeout(run, 1500));
  };

  return (
    <section className={`sa ${searched ? "searched" : ""}`}>
      <div className="ed-wrap">
        {!searched && <span className="eyebrow">Assistant d&apos;achat · IA</span>}
        <h1>{searched ? "Que voulez-vous comparer ensuite ?" : "Que souhaitez-vous acheter aujourd'hui ?"}</h1>

        <form
          className="sa-search"
          onSubmit={(e) => {
            e.preventDefault();
            ask(query || "iPhone 18 Pro");
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
              placeholder="iPhone 18 Pro, Dyson V15, PS6…"
              aria-label="Que voulez-vous acheter ?"
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
              <span className="sa-orb" /> FILON analyse les offres…
            </div>
          )}
          {!thinking && searched && (
            <>
              <div className="sa-card">
                <div className="sa-head">
                  <span className="sa-dot" /> <b>FILON</b> · conseil d&apos;achat <span className="cnt sa-cnt" />
                </div>
                <p className="sa-text" />
              </div>
              <div className="sa-results" />
              <div className="sa-verdict">
                <div>
                  <div className="lab">Votre prix réel le plus bas</div>
                  <div className="price mono sa-vp">—</div>
                </div>
                <div className="sv sa-vs" />
                <a className="ed-btn wave" href="/#installer">Voir l&apos;offre</a>
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
