"use client";

// Bande de preuves (home) — logos marchands rendus en noms stylés (pas de
// fichiers logos à héberger, aucune marque déposée récupérée), prix réel
// décomposé (exemple balisé), faits de transparence, emplacement d'avis.
// Aucun chiffre inventé : montants marqués « exemple », repère • réservé aux
// vrais chiffres post-partenariats.

import { useEffect, useRef, useState } from "react";
import { Reveal } from "./Reveal";
import { useLocale } from "@/lib/i18n";

const MERCHANTS = [
  { name: "Amazon", src: "/logos/amazon.webp" },
  { name: "Fnac", src: "/logos/fnac.webp" },
  { name: "Cdiscount", src: "/logos/cdiscount.webp" },
  { name: "Boulanger", src: "/logos/boulanger.webp" },
  { name: "Darty", src: "/logos/darty.svg" },
  { name: "Rakuten", src: "/logos/rakuten.webp" },
];

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

const PL = {
  fr: {
    eye: "FILON compare, en temps réel",
    note: "Et des dizaines d'autres marchands, plus les vendeurs reconditionnés certifiés.",
    stats: STATS,
    legend2: "se rempliront avec des chiffres réels dès l'ouverture des partenariats.",
    legend1: "Les repères marqués",
    priceEye: "Le vrai prix, décomposé",
    priceH1: "L'étiquette n'est jamais ", priceH2: "le prix réel.",
    priceP: "FILON part du prix affiché, puis retire ce que vous pouvez vraiment récupérer, coupon vérifié, cashback, meilleur marchand, pour révéler le montant que vous paierez réellement.",
    ex: "Exemple illustratif · Lenovo IdeaPad Slim 5",
    breakdown: BREAKDOWN,
    total: "Vrai prix FILON",
    trust: TRUST,
  },
  nl: {
    eye: "FILON vergelijkt, in realtime",
    note: "En tientallen andere winkels, plus gecertificeerde refurbished-verkopers.",
    stats: [
      ["5+", "grote winkels vergeleken bij elke zoekopdracht"],
      ["3-in-1", "prijs + kortingscodes + cashback, samengevoegd tot één prijs"],
      ["0 €", "je betaalt FILON nooit, nooit reclame", "g"],
      ["•", "gebruikers & bespaarde €, echte cijfers volgen", "dot"],
    ] as Array<[string, string, string?]>,
    legend1: "De met",
    legend2: "gemarkeerde punten worden ingevuld met echte cijfers zodra de partnerships starten.",
    priceEye: "De echte prijs, ontleed",
    priceH1: "Het prijskaartje is nooit ", priceH2: "de echte prijs.",
    priceP: "FILON vertrekt van de getoonde prijs en trekt er af wat je echt kunt recupereren — geverifieerde code, cashback, beste winkel — om te tonen wat je werkelijk betaalt.",
    ex: "Illustratief voorbeeld · Lenovo IdeaPad Slim 5",
    breakdown: [
      ["Getoonde prijs op deze pagina", "799 €", false],
      ["Beste winkel gevonden", "−60 €", true],
      ["Geverifieerde code bij betaling", "−15 €", true],
      ["Uitgekeerde cashback", "−25 €", true],
    ] as Array<[string, string, boolean]>,
    total: "Echte FILON-prijs",
    trust: [
      ["Geen plaats te koop", "Geen enkel merk of winkel kan betalen voor een betere rangschikking of Score. Nooit."],
      ["Gratis, en aan jouw kant", "Onze vergoeding komt uit affiliatie, zonder ooit je prijs te verhogen of een advies te vervalsen."],
      ["Je gegevens blijven van jou", "Analytics zonder cookies, geen doorverkoop. Wat je zoekt verlaat FILON nooit."],
    ] as Array<[string, string]>,
  },
};

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

/** Bannière vivante : vidéo d'unboxing en boucle, poster + repli sans animation. */
function LifeBanner() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  return (
    <Reveal className="ed-proof-life">
      {reduced ? (
        <img src="/img/proof-unboxing.webp" alt="" loading="lazy" />
      ) : (
        <video autoPlay muted loop playsInline poster="/img/proof-unboxing.webp" aria-hidden="true">
          <source src="/video/unboxing.mp4" type="video/mp4" />
        </video>
      )}
    </Reveal>
  );
}

export function ProofSection() {
  const { locale } = useLocale();
  const x = PL[locale];
  return (
    <section className="ed-band ed-proof" id="preuves">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", textAlign: "center" }}>
            {x.eye}
          </span>
        </Reveal>

        <Reveal className="ed-proof-marquee">
          <div className="track">
            {[...MERCHANTS, ...MERCHANTS].map((m, i) => (
              <div className="ed-proof-logo" key={`${m.name}-${i}`}>
                <img src={m.src} alt={m.name} loading="lazy" />
              </div>
            ))}
          </div>
        </Reveal>
        <Reveal>
          <p className="ed-proof-note">
            {x.note}
          </p>
        </Reveal>

        <Reveal className="ed-proof-stats">
          {x.stats.map(([value, label, mod]) => (
            <div key={label}>
              <div className={`ed-proof-stat-v ${mod === "g" ? "g" : mod === "dot" ? "dot" : ""}`}>{value}</div>
              <div className="ed-proof-stat-l">{label}</div>
            </div>
          ))}
        </Reveal>
        <Reveal>
          <p className="ed-proof-legend">
            {x.legend1} <span className="dot">•</span> {x.legend2}
          </p>
        </Reveal>

        <LifeBanner />

        <div className="ed-proof-price">
          <Reveal className="ed-proof-price-copy">
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>
              {x.priceEye}
            </span>
            <h2>
              {x.priceH1}<span className="it">{x.priceH2}</span>
            </h2>
            <p>{x.priceP}</p>
          </Reveal>
          <Reveal className="ed-proof-card">
            <div className="ex">{x.ex}</div>
            {x.breakdown.map(([label, value, good]) => (
              <div className="row" key={label}>
                <span>{label}</span>
                <span className={good ? "v good" : "v"}>{value}</span>
              </div>
            ))}
            <div className="total">
              <span>{x.total}</span>
              <PriceCountUp />
            </div>
          </Reveal>
        </div>

        <div className="ed-proof-trust">
          {x.trust.map(([title, body]) => (
            <Reveal className="ed-proof-tcard" key={title}>
              <h3>{title}</h3>
              <p>{body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
