"use client";

// Bande de preuves (home) — logos marchands rendus en noms stylés (pas de
// fichiers logos à héberger, aucune marque déposée récupérée), prix réel
// décomposé (exemple balisé), faits de transparence, emplacement d'avis.
// Aucun chiffre inventé : montants marqués « exemple », repère • réservé aux
// vrais chiffres post-partenariats.

import { useEffect, useRef, useState } from "react";
import { Reveal } from "./Reveal";

const MERCHANTS = ["Amazon", "Fnac", "Cdiscount", "Boulanger", "Darty", "Rakuten", "Coolblue", "MediaMarkt"];

const STATS: Array<[string, string, string?]> = [
  ["5+", "grands marchands comparés à chaque recherche"],
  ["3-en-1", "prix + coupons + cashback, fusionnés en un seul prix"],
  ["0 €", "vous ne payez jamais FILON, jamais de pub", "g"],
  ["•", "utilisateurs & € économisés, chiffres réels à venir", "dot"],
];

const BREAKDOWN: Array<[string, string, boolean]> = [
  ["Prix affiché sur cette page", "799 €", false],
  ["Meilleur marchand trouvé", "−60 €", true],
  ["Coupon vérifié au paiement", "−15 €", true],
  ["Cashback reversé", "−25 €", true],
];

const TRUST: Array<[string, string]> = [
  ["Aucune place ne s'achète", "Aucune marque ni marchand ne peut payer pour un meilleur classement ou un meilleur Score. Jamais."],
  ["Gratuit, et de votre côté", "Notre rémunération vient de l'affiliation, sans jamais augmenter votre prix, ni fausser un conseil."],
  ["Vos données restent à vous", "Analytics sans cookies, aucune revente. Ce que vous cherchez ne quitte jamais FILON."],
];

function PriceCountUp() {
  const ref = useRef<HTMLSpanElement>(null);
  const [txt, setTxt] = useState("799 €");
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setTxt("699 €");
      return;
    }
    let done = false;
    const run = () => {
      if (done) return;
      done = true;
      const from = 799;
      const to = 699;
      const dur = 900;
      const t0 = performance.now();
      const step = (t: number) => {
        const p = Math.min(1, (t - t0) / dur);
        const v = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
        setTxt(v.toLocaleString("fr-FR") + " €");
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && (run(), io.disconnect())),
      { threshold: 0.4 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <span ref={ref} className="ed-proof-total-val">{txt}</span>;
}

export function ProofSection() {
  return (
    <section className="ed-band ed-proof" id="preuves">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", textAlign: "center" }}>
            FILON compare, en temps réel
          </span>
        </Reveal>

        <Reveal className="ed-proof-marquee">
          <div className="track">
            {[...MERCHANTS, ...MERCHANTS].map((name, i) => (
              <div className="ed-proof-logo" key={`${name}-${i}`}>
                <span>{name}</span>
              </div>
            ))}
          </div>
        </Reveal>
        <Reveal>
          <p className="ed-proof-note">
            Et des dizaines d'autres marchands, plus les vendeurs reconditionnés certifiés.
          </p>
        </Reveal>

        <Reveal className="ed-proof-stats">
          {STATS.map(([value, label, mod]) => (
            <div key={label}>
              <div className={`ed-proof-stat-v ${mod === "g" ? "g" : mod === "dot" ? "dot" : ""}`}>{value}</div>
              <div className="ed-proof-stat-l">{label}</div>
            </div>
          ))}
        </Reveal>
        <Reveal>
          <p className="ed-proof-legend">
            Les repères marqués <span className="dot">•</span> se rempliront avec des chiffres réels
            dès l'ouverture des partenariats.
          </p>
        </Reveal>

        <div className="ed-proof-price">
          <Reveal className="ed-proof-price-copy">
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>
              Le vrai prix, décomposé
            </span>
            <h2>
              L'étiquette n'est jamais <span className="it">le prix réel.</span>
            </h2>
            <p>
              FILON part du prix affiché, puis retire ce que vous pouvez vraiment récupérer,
              coupon vérifié, cashback, meilleur marchand, pour révéler le montant que vous
              paierez réellement.
            </p>
          </Reveal>
          <Reveal className="ed-proof-card">
            <div className="ex">Exemple illustratif · Lenovo IdeaPad Slim 5</div>
            {BREAKDOWN.map(([label, value, good]) => (
              <div className="row" key={label}>
                <span>{label}</span>
                <span className={good ? "v good" : "v"}>{value}</span>
              </div>
            ))}
            <div className="total">
              <span>Vrai prix FILON</span>
              <PriceCountUp />
            </div>
          </Reveal>
        </div>

        <div className="ed-proof-trust">
          {TRUST.map(([title, body]) => (
            <Reveal className="ed-proof-tcard" key={title}>
              <h3>{title}</h3>
              <p>{body}</p>
            </Reveal>
          ))}
        </div>

        <Reveal className="ed-proof-slot">
          <span className="eyebrow">Emplacement · avis vérifiés</span>
          <p className="q">
            « Les vrais témoignages utilisateurs et la note moyenne viendront ici, après les
            premiers milliers d'achats. »
          </p>
          <p className="warn">À ne jamais remplir avec de faux avis. La neutralité est notre seul actif.</p>
        </Reveal>
      </div>
    </section>
  );
}
