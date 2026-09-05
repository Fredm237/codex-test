"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import type { Proof } from "@/lib/proof";
import { formatSupportedMoney } from "@/lib/currency";
import { useLocale } from "@/lib/i18n";
import { HomeSignatureVolume, type HomeVolumeState } from "./HomeSignatureVolume";
import { ProductJourneyLink } from "./ProductJourneyLink";
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
    high: "Prix le plus haut",
    low: "Meilleur prix",
    view: "Voir le produit",
    verified: "Même produit · prix vérifiés",
    unavailable: "La comparaison apparaîtra dès qu’un produit exact sera vérifié.",
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
    high: "Hoogste prijs",
    low: "Beste prijs",
    view: "Bekijk het product",
    verified: "Zelfde product · prijzen gecontroleerd",
    unavailable: "De vergelijking verschijnt zodra een exact product is gecontroleerd.",
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
    high: "Highest price",
    low: "Best price",
    view: "View product",
    verified: "Same product · prices checked",
    unavailable: "The comparison will appear once an exact product has been verified.",
    replay: "Replay",
  },
} as const;

const NUMBER_LOCALE = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

export function CommerceJourney({ exactProduct, proof }: { exactProduct: ImmersiveExactProductProof | null; proof: Proof | null }) {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const product = exactProduct ?? proof?.product ?? null;
  const low = product ? formatSupportedMoney(product.priceMin, product.currency, locale) : null;
  const high = product ? formatSupportedMoney(product.priceMax, product.currency, locale) : null;
  const comparable = Boolean(product && low && high);
  const [progress, setProgress] = useState(0);
  const [shot, setShot] = useState(0);
  const [reduced, setReduced] = useState(false);
  const [cycle, setCycle] = useState(0);
  const [volumeState, setVolumeState] = useState<HomeVolumeState>("pending");
  const startedAt = useRef(0);
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
    startedAt.current = performance.now();
    const play = (now: number) => {
      const next = Math.min(1, (now - startedAt.current) / 12_800);
      setProgress(next);
      setShot(next < .22 ? 0 : next < .48 ? 1 : next < .76 ? 2 : 3);
      if (next < 1) frame = requestAnimationFrame(play);
    };
    frame = requestAnimationFrame(play);
    return () => cancelAnimationFrame(frame);
  }, [cycle]);

  const handleVolumeState = useCallback((state: HomeVolumeState) => setVolumeState(state), []);
  const replay = () => {
    setProgress(0);
    setShot(0);
    setCycle((value) => value + 1);
  };

  return (
    <section className={`${styles.world} p11-web-experience`} data-shot={shot} data-reduced={reduced} data-immersive-journey aria-labelledby="filon-home-title">
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
        <div className={styles.stage} data-volume={volumeState}>
          <HomeSignatureVolume onStateChange={handleVolumeState} product={comparable ? product : null} progress={progress} reduced={reduced} />
          <div className={styles.stats} aria-hidden="true">
            <span><b>{proof ? number.format(proof.stats.offers) : "—"}</b>{copy.offers}</span>
            <span><b>{proof ? number.format(proof.stats.merchants) : "—"}</b>{copy.merchants}</span>
          </div>
          {comparable && product?.image && low && high ? (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className={styles.product} src={product.image} alt={product.name} fetchPriority="high" decoding="async" />
              <div className={`${styles.price} ${styles.priceHigh}`}><small>{copy.high}</small><b>{high}</b></div>
              <div className={`${styles.price} ${styles.priceLow}`}><small>{copy.low}</small><b>{low}</b></div>
              <div className={styles.decision}>
                <small>{copy.verified}</small>
                <strong>{product.brand ? `${product.brand} · ` : ""}{product.name}</strong>
                <ProductJourneyLink href={`/produits/${encodeURIComponent(product.ean)}/`} image={product.image} label={product.name}>{copy.view} →</ProductJourneyLink>
              </div>
            </>
          ) : <p className={styles.unknown}>{copy.unavailable}</p>}
        </div>
      </div>
    </section>
  );
}
