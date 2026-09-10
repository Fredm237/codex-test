"use client";

import { useEffect, useRef, useState } from "react";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { CinematicSequenceRenderer } from "@/components/cinematic/CinematicSequenceRenderer";
import type { SequenceDefinition } from "@/components/cinematic/types";
import styles from "./commerce-journey.module.css";

const COPY = {
  fr: {
    eyebrow: "Comparer devient simple",
    title: ["Vous cherchez.", "FILON reconnaît.", "Les offres se rapprochent.", "Vous choisissez."],
    detail: [
      "Un produit, une marque ou simplement votre besoin.",
      "La référence exacte reste au centre. Aucun produit ressemblant n’est mélangé.",
      "Seuls les prix réellement comparables restent visibles.",
      "Le meilleur prix et ses preuves apparaissent ensemble.",
    ],
    searchLabel: "Que cherchez-vous aujourd’hui ?",
    placeholder: "Un ordinateur, une montre, un canapé…",
    submit: "Trouver",
    catalogue: "Voir le catalogue",
    offers: "offres suivies",
    merchants: "marchands",
    replay: "Rejouer",
  },
  nl: {
    eyebrow: "Vergelijken wordt eenvoudig",
    title: ["U zoekt.", "FILON herkent.", "Aanbiedingen komen samen.", "U kiest."],
    detail: [
      "Een product, een merk of gewoon wat u nodig hebt.",
      "De exacte referentie blijft centraal. Geen gelijkend product wordt gemengd.",
      "Alleen werkelijk vergelijkbare prijzen blijven zichtbaar.",
      "De beste prijs en het bewijs verschijnen samen.",
    ],
    searchLabel: "Wat zoekt u vandaag?",
    placeholder: "Een laptop, horloge, bank…",
    submit: "Zoeken",
    catalogue: "Bekijk de catalogus",
    offers: "gevolgde aanbiedingen",
    merchants: "winkels",
    replay: "Opnieuw",
  },
  en: {
    eyebrow: "Comparison, made simple",
    title: ["You search.", "FILON recognises.", "Offers come together.", "You choose."],
    detail: [
      "A product, a brand or simply what you need.",
      "The exact reference stays at the centre. Similar products are never mixed in.",
      "Only genuinely comparable prices remain visible.",
      "The best price and its evidence appear together.",
    ],
    searchLabel: "What are you looking for today?",
    placeholder: "A laptop, watch, sofa…",
    submit: "Find it",
    catalogue: "Browse the catalogue",
    offers: "offers tracked",
    merchants: "merchants",
    replay: "Replay",
  },
} as const;

const NUMBER_LOCALE = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

const INDUSTRIAL_COPY = {
  fr: {
    eyebrow: "Le marché, mis au clair",
    title: ["Vous cherchez.", "FILON traverse le marché.", "Le vrai produit reste.", "Vous choisissez."],
    detail: [
      "Un ordinateur, un canapé, une poussette… Le marché vous présente trop de choix.",
      "FILON rassemble les offres et écarte celles qui ne parlent pas du même produit.",
      "Même référence, prix comparables, marchands vérifiés : tout s’aligne.",
      "Le meilleur prix et ses preuves arrivent ensemble. La décision vous appartient.",
    ],
    scroll: "Faites défiler pour voir FILON agir",
    decisionLabel: "Une seule référence à la fois",
    decisionTitle: "Comparez sans mélanger les produits.",
    decisionCta: "Chercher un produit",
  },
  nl: {
    eyebrow: "De markt, helder gemaakt",
    title: ["U zoekt.", "FILON doorkruist de markt.", "Het juiste product blijft.", "U kiest."],
    detail: [
      "Een laptop, bank of kinderwagen… De markt geeft u te veel keuzes.",
      "FILON verzamelt aanbiedingen en verwijdert wat niet exact hetzelfde product is.",
      "Dezelfde referentie, vergelijkbare prijzen en gecontroleerde winkels komen op één lijn.",
      "De beste prijs en het bewijs komen samen. U beslist.",
    ],
    scroll: "Scroll om FILON aan het werk te zien",
    decisionLabel: "Eén referentie tegelijk",
    decisionTitle: "Vergelijk zonder producten te vermengen.",
    decisionCta: "Zoek een product",
  },
  en: {
    eyebrow: "The market, made clear",
    title: ["You search.", "FILON crosses the market.", "The right product remains.", "You choose."],
    detail: [
      "A laptop, sofa or stroller… The market gives you too many choices.",
      "FILON gathers the offers and removes anything that is not the exact same product.",
      "The same reference, comparable prices and checked merchants fall into line.",
      "The best price and its proof arrive together. The decision is yours.",
    ],
    scroll: "Scroll to see FILON work",
    decisionLabel: "One exact reference at a time",
    decisionTitle: "Compare without mixing products.",
    decisionCta: "Search for a product",
  },
} as const;

const INDUSTRIAL_SEQUENCE = {
  frameBase: "/cinematic/filon-scroll-story/desktop-v7-sprites4",
  frames: 363,
  poster: "/cinematic/filon-scroll-story/desktop-v7-sprites4/poster-first.webp",
  finalPoster: "/cinematic/filon-scroll-story/desktop-v7-sprites4/poster-final.webp",
  scrollHeightVh: 390,
  frameStride: 1,
  sprite: {
    framesPerSheet: 4,
    columns: 2,
    rows: 2,
    tileWidth: 1280,
    tileHeight: 720,
  },
} satisfies SequenceDefinition;

export function CommerceJourney({ proof }: { proof: Proof | null }) {
  const { locale } = useLocale();
  const industrialCopy = INDUSTRIAL_COPY[locale];
  const copy = { ...COPY[locale], ...industrialCopy };
  const scrollCopy = industrialCopy.scroll;
  const [progress, setProgress] = useState(0);
  const [shot, setShot] = useState(0);
  const [reduced, setReduced] = useState(false);
  const journey = useRef<HTMLElement>(null);
  const number = new Intl.NumberFormat(NUMBER_LOCALE[locale]);

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const saveData = Boolean((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData);
    const shouldReduce = motion.matches || saveData;
    setReduced(shouldReduce);
    if (shouldReduce) {
      setProgress(1);
      setShot(3);
      return;
    }
    let frame = 0;
    const updateFromScroll = () => {
      const element = journey.current;
      if (!element) return;
      const bounds = element.getBoundingClientRect();
      const start = window.scrollY + bounds.top;
      const range = Math.max(1, element.offsetHeight - window.innerHeight);
      const next = Math.max(0, Math.min(1, (window.scrollY - start) / range));
      setProgress(next);
      setShot(next < .22 ? 0 : next < .48 ? 1 : next < .76 ? 2 : 3);
    };
    const requestUpdate = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(updateFromScroll);
    };
    requestUpdate();
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", requestUpdate);
      window.removeEventListener("resize", requestUpdate);
    };
  }, []);

  const replay = () => {
    journey.current?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  };

  return (
    <section ref={journey} className={`${styles.world} p11-web-experience`} data-shot={shot} data-direction="industrial" data-reduced={reduced} data-immersive-journey aria-labelledby="filon-home-title">
      <div className={styles.frame}>
        <div className={styles.cinematicPlates} aria-hidden="true">
          <CinematicSequenceRenderer
            sequence={INDUSTRIAL_SEQUENCE}
            frameProgress={progress}
            cameraProgress={.5}
            reducedMotion={reduced}
            className={styles.frameSequence}
          />
          <div className={styles.cinematicShade} />
        </div>
        <div className={styles.sky} aria-hidden="true" />
        <div className={styles.layout}>
        <div className={styles.copy}>
          <p className={styles.eyebrow}>{copy.eyebrow}</p>
          <h1 id="filon-home-title">{copy.title[shot]}</h1>
          <p className={styles.detail}>{copy.detail[shot]}</p>
          <form className={styles.search} action="/recherche/" method="get" role="search">
            <label htmlFor="home-commerce-query">{copy.searchLabel}</label>
            <div>
              <input id="home-commerce-query" name="q" type="search" minLength={2} placeholder={copy.placeholder} autoComplete="off" />
              <button type="submit">{copy.submit}</button>
            </div>
          </form>
          {shot === 0 ? <p className={styles.scrollCue}>{scrollCopy} <span aria-hidden="true">↓</span></p> : null}
          <div className={styles.timeline} aria-label={copy.title.join(" ")}>
            {copy.title.map((label, index) => (
              <span key={label} data-active={index === shot} data-past={index < shot}>
                <i aria-hidden="true" /><b>0{index + 1}</b><em>{label}</em>
              </span>
            ))}
            {!reduced && progress === 1 ? <button type="button" onClick={replay} aria-label={copy.replay}>↻</button> : null}
          </div>
          <a className={styles.catalogue} href="/catalogue/">{copy.catalogue} <span aria-hidden="true">→</span></a>
        </div>
        <div className={styles.stage}>
          <div className={styles.stats} aria-hidden="true">
            <span><b>{proof ? number.format(proof.stats.offers) : "—"}</b>{copy.offers}</span>
            <span><b>{proof ? number.format(proof.stats.merchants) : "—"}</b>{copy.merchants}</span>
          </div>
          <div className={styles.decision} data-industrial-decision>
            <small>{industrialCopy.decisionLabel}</small>
            <strong>{industrialCopy.decisionTitle}</strong>
            <a href="/recherche/">{industrialCopy.decisionCta} →</a>
          </div>
        </div>
      </div>
      </div>
    </section>
  );
}
