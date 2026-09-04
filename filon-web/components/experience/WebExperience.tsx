"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Proof } from "@/lib/proof";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import { formatSupportedMoney } from "@/lib/currency";
import { useLocale } from "@/lib/i18n";
import {
  ConstraintSummary,
  DecisionCard,
  EvidenceBadge,
  OfferComparison,
  TradeoffCard,
  UnknownField,
  WhyThisResult,
} from "./DecisionPrimitives";
import styles from "./web-experience.module.css";
import { HomeSignatureVolume, type HomeVolumeState } from "./HomeSignatureVolume";
import { ProductJourneyLink } from "./ProductJourneyLink";
import { SkipLink } from "@/components/editorial/SkipLink";

const COPY = {
  fr: {
    eyebrow: "Votre comparateur · preuves à l’appui",
    titleA: "Le bon produit.",
    titleB: "Les prix sous les yeux.",
    lead: "FILON vérifie qu’il s’agit bien du même produit, compare les offres disponibles et vous montre d’où viennent les prix.",
    searchLabel: "Quel produit cherchez-vous ?",
    searchPlaceholder: "Ex. casque Sony WH-1000XM5",
    search: "Comparer",
    catalogue: "Explorer le catalogue",
    boundary: "Pas de promesse inventée : si FILON ne sait pas, il vous le dit.",
    proofKicker: "Catalogue actif",
    proofTitle: "Ce que FILON compare aujourd’hui",
    proofNote: "Ces chiffres suivent automatiquement les nouvelles offres et les marchands suivis par FILON.",
    offers: "offres comparées",
    merchants: "marchands suivis",
    comparable: "produits disponibles chez plusieurs marchands",
    exampleEye: "Choisi dans le catalogue",
    exampleReady: "Ce produit est comparé",
    exampleUnknown: "Comparaison indisponible",
    verified: "Vérifié",
    unknown: "Inconnu",
    identity: "Même produit",
    current: "Informations vérifiées",
    scope: "Plusieurs marchands",
    high: "Prix le plus haut",
    low: "Prix le plus bas",
    spread: "Différence de prix",
    compareTitle: "Les prix de ce produit",
    observed: (date: string) => `Prix relevés ${date}`,
    why: "Pourquoi vous pouvez comparer",
    reasons: (ean: string, merchants: number) => [
      `Même référence produit : EAN ${ean}.`,
      `${merchants} marchands proposent ce produit.`,
      "Les prix récents sont affichés dans la même devise.",
    ],
    view: "Voir le produit et les offres",
    unavailable: "Aucun produit comparable n’est disponible pour le moment.",
    unavailableDetail: "FILON préfère ne rien afficher plutôt que d’inventer un produit ou un prix.",
    methodEye: "Simple à lire, sérieux derrière",
    methodTitle: "FILON vérifie avant de comparer.",
    steps: [
      ["Même produit", "FILON s’assure que toutes les offres concernent exactement le même produit."],
      ["Informations à jour", "Le prix, la disponibilité, la date et le marchand sont contrôlés."],
      ["Résultat clair", "Vous voyez ce qui est vérifié et ce qui manque encore."],
    ],
    constraints: "Vérifications effectuées",
    closing: "Que cherchez-vous aujourd’hui ?",
    closingBody: "Saisissez un produit, une marque ou votre besoin. FILON rassemble les offres qui peuvent vraiment être comparées.",
    skipJourney: "Passer l’expérience",
    journey: [
      "Tout commence par votre produit.",
      "FILON retrouve la référence exacte.",
      "Les offres comparables se rapprochent.",
      "Vous voyez clairement les écarts.",
    ],
    journeyUnknown: [
      "Tout commence par votre produit.",
      "La référence doit encore être confirmée.",
      "Les prix ne peuvent pas encore être comparés.",
      "FILON vous le dit clairement.",
    ],
    journeySummary: "Le parcours montre comment FILON retrouve le bon produit, rassemble ses offres et compare leurs prix. La recherche reste disponible à tout moment.",
  },
  nl: {
    eyebrow: "Uw vergelijker · met bewijs",
    titleA: "Het juiste product.",
    titleB: "Alle prijzen in beeld.",
    lead: "FILON controleert of het echt om hetzelfde product gaat, vergelijkt beschikbare aanbiedingen en toont waar de prijzen vandaan komen.",
    searchLabel: "Welk product zoekt u?",
    searchPlaceholder: "Bijv. Sony WH-1000XM5 hoofdtelefoon",
    search: "Vergelijken",
    catalogue: "Catalogus verkennen",
    boundary: "Geen verzonnen beloftes: als FILON iets niet weet, zegt het dat.",
    proofKicker: "Actieve catalogus",
    proofTitle: "Wat FILON vandaag vergelijkt",
    proofNote: "Deze cijfers volgen automatisch de nieuwe aanbiedingen en winkels die FILON opvolgt.",
    offers: "vergeleken aanbiedingen",
    merchants: "gevolgde winkels",
    comparable: "producten bij meerdere winkels",
    exampleEye: "Gekozen uit de catalogus",
    exampleReady: "Dit product wordt vergeleken",
    exampleUnknown: "Vergelijking niet beschikbaar",
    verified: "Geverifieerd",
    unknown: "Onbekend",
    identity: "Hetzelfde product",
    current: "Gecontroleerde informatie",
    scope: "Meerdere winkels",
    high: "Hoogste prijs",
    low: "Laagste prijs",
    spread: "Prijsverschil",
    compareTitle: "De prijzen van dit product",
    observed: (date: string) => `Prijzen gemeten ${date}`,
    why: "Waarom u kunt vergelijken",
    reasons: (ean: string, merchants: number) => [
      `Dezelfde productreferentie: EAN ${ean}.`,
      `${merchants} winkels bieden dit product aan.`,
      "Recente prijzen worden in dezelfde valuta getoond.",
    ],
    view: "Bekijk product en aanbiedingen",
    unavailable: "Er is momenteel geen vergelijkbaar product beschikbaar.",
    unavailableDetail: "FILON toont liever niets dan een product of prijs te verzinnen.",
    methodEye: "Eenvoudig om te lezen, grondig erachter",
    methodTitle: "FILON controleert vóór het vergelijken.",
    steps: [
      ["Hetzelfde product", "FILON controleert of alle aanbiedingen exact hetzelfde product betreffen."],
      ["Actuele informatie", "Prijs, beschikbaarheid, datum en winkel worden gecontroleerd."],
      ["Duidelijk resultaat", "U ziet wat gecontroleerd is en wat nog ontbreekt."],
    ],
    constraints: "Uitgevoerde controles",
    closing: "Wat zoekt u vandaag?",
    closingBody: "Voer een product, merk of behoefte in. FILON verzamelt de aanbiedingen die echt vergelijkbaar zijn.",
    skipJourney: "Ervaring overslaan",
    journey: [
      "Alles begint met uw product.",
      "FILON vindt de exacte referentie.",
      "Vergelijkbare aanbiedingen komen samen.",
      "U ziet de verschillen meteen.",
    ],
    journeyUnknown: [
      "Alles begint met uw product.",
      "De referentie moet nog worden bevestigd.",
      "De prijzen kunnen nog niet worden vergeleken.",
      "FILON zegt het duidelijk.",
    ],
    journeySummary: "Het traject toont hoe FILON het juiste product vindt, aanbiedingen verzamelt en prijzen vergelijkt. Zoeken blijft altijd beschikbaar.",
  },
  en: {
    eyebrow: "Your comparison guide · backed by evidence",
    titleA: "The right product.",
    titleB: "Every price in view.",
    lead: "FILON checks that each offer is for the same product, compares what is available and shows where every price comes from.",
    searchLabel: "What product are you looking for?",
    searchPlaceholder: "E.g. Sony WH-1000XM5 headphones",
    search: "Compare",
    catalogue: "Explore the catalogue",
    boundary: "No invented promises: if FILON does not know, it tells you.",
    proofKicker: "Active catalogue",
    proofTitle: "What FILON compares today",
    proofNote: "These figures automatically follow the new offers and merchants tracked by FILON.",
    offers: "offers compared",
    merchants: "merchants tracked",
    comparable: "products available from several merchants",
    exampleEye: "Chosen from the catalogue",
    exampleReady: "This product is being compared",
    exampleUnknown: "Comparison unavailable",
    verified: "Verified",
    unknown: "Unknown",
    identity: "Same product",
    current: "Checked information",
    scope: "Several merchants",
    high: "Highest price",
    low: "Lowest price",
    spread: "Price difference",
    compareTitle: "Prices for this product",
    observed: (date: string) => `Prices checked ${date}`,
    why: "Why you can compare",
    reasons: (ean: string, merchants: number) => [
      `Same product reference: EAN ${ean}.`,
      `${merchants} merchants offer this product.`,
      "Recent prices are shown in the same currency.",
    ],
    view: "View product and offers",
    unavailable: "No comparable product is available right now.",
    unavailableDetail: "FILON would rather show nothing than invent a product or price.",
    methodEye: "Simple to read, rigorous behind the scenes",
    methodTitle: "FILON checks before it compares.",
    steps: [
      ["Same product", "FILON makes sure every offer is for exactly the same product."],
      ["Up-to-date information", "Price, availability, date and merchant are checked."],
      ["Clear result", "You see what has been checked and what is still missing."],
    ],
    constraints: "Checks completed",
    closing: "What are you looking for today?",
    closingBody: "Enter a product, brand or need. FILON brings together the offers that can genuinely be compared.",
    skipJourney: "Skip the experience",
    journey: [
      "It all starts with your product.",
      "FILON finds the exact reference.",
      "Comparable offers come together.",
      "The price differences become clear.",
    ],
    journeyUnknown: [
      "It all starts with your product.",
      "The reference still needs confirmation.",
      "The prices cannot be compared yet.",
      "FILON tells you clearly.",
    ],
    journeySummary: "The journey shows how FILON finds the right product, gathers its offers and compares their prices. Search remains available at all times.",
  },
} as const;

const NUMBER_LOCALE = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

export function WebExperience({ exactProduct, proof }: { exactProduct: ImmersiveExactProductProof | null; proof: Proof | null }) {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const journeyRef = useRef<HTMLElement | null>(null);
  const [journeyShot, setJourneyShot] = useState(0);
  const [journeyProgress, setJourneyProgress] = useState(0);
  const [reducedJourney, setReducedJourney] = useState(false);
  const [volumeState, setVolumeState] = useState<HomeVolumeState>("pending");
  const product = exactProduct ?? proof?.product ?? null;
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, locale) : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, locale) : null;
  const spread = product ? formatSupportedMoney(product.priceMax - product.priceMin, product.currency, locale) : null;
  const comparable = Boolean(product && priceLow && priceHigh && spread);
  const journeyLines = comparable ? copy.journey : copy.journeyUnknown;
  const number = new Intl.NumberFormat(NUMBER_LOCALE[locale]);
  const observedDate = exactProduct?.latestObservedAt
    ? new Intl.DateTimeFormat(NUMBER_LOCALE[locale], {
      dateStyle: "long",
      timeStyle: "short",
      timeZone: "Europe/Brussels",
    }).format(new Date(exactProduct.latestObservedAt))
    : null;

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    let frame = 0;

    const update = () => {
      frame = 0;
      const reduced = motion.matches || Boolean(connection?.saveData);
      setReducedJourney(reduced);
      if (reduced) {
        setJourneyShot(3);
        setJourneyProgress(1);
        return;
      }
      const root = journeyRef.current;
      if (!root) return;
      const rect = root.getBoundingClientRect();
      const distance = Math.max(1, root.offsetHeight - window.innerHeight);
      const progress = Math.max(0, Math.min(1, -rect.top / distance));
      setJourneyProgress(progress);
      setJourneyShot(progress < .24 ? 0 : progress < .49 ? 1 : progress < .74 ? 2 : 3);
    };

    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    motion.addEventListener("change", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      motion.removeEventListener("change", schedule);
      cancelAnimationFrame(frame);
    };
  }, []);

  const handleVolumeState = useCallback((state: HomeVolumeState) => setVolumeState(state), []);

  return (
    <div className={`${styles.page} p11-web-experience`}>
      <section ref={journeyRef} className={styles.hero} aria-labelledby="home-title" data-immersive-journey data-reduced={reducedJourney}>
        <SkipLink className={styles.skipJourney} targetId="home-after-journey">
          {copy.skipJourney}
        </SkipLink>
        <div className={styles.heroSticky} data-shot={journeyShot}>
          <div className={styles.heroGlow} aria-hidden="true" />
          <div className={`${styles.wrap} ${styles.heroGrid}`}>
            <div className={styles.heroCopy}>
              <EvidenceBadge state="verified">{copy.eyebrow}</EvidenceBadge>
              <h1 id="home-title"><span>{copy.titleA}</span>{copy.titleB}</h1>
              <div className={styles.journeyCopy} aria-hidden="true">
                {journeyLines.map((line, index) => <p key={line} data-active={journeyShot === index}>{line}</p>)}
              </div>
              <p className={styles.lead}>{copy.lead}</p>
              <form className={styles.search} action="/recherche/" method="get" role="search">
                <label htmlFor="home-query">{copy.searchLabel}</label>
                <div>
                  <input id="home-query" type="search" name="q" minLength={2} placeholder={copy.searchPlaceholder} autoComplete="off" />
                  <button type="submit">{copy.search}</button>
                </div>
              </form>
              <div className={styles.actions}>
                <a href="/catalogue/">{copy.catalogue}</a>
                <p>{copy.boundary}</p>
              </div>
            </div>
            <aside className={styles.heroStage} aria-label={copy.exampleEye} data-volume={volumeState}>
              <HomeSignatureVolume
                onStateChange={handleVolumeState}
                product={comparable ? product : null}
                progress={journeyProgress}
                reduced={reducedJourney}
              />
              <div className={styles.marketFragments} aria-hidden="true">
                <span>{proof ? number.format(proof.stats.offers) : "?"}<small>{copy.offers}</small></span>
                <span>{proof ? number.format(proof.stats.merchants) : "?"}<small>{copy.merchants}</small></span>
                <span>{product?.ean ?? "?"}<small>EAN</small></span>
              </div>
              {comparable && product?.image && priceLow && priceHigh ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={product.image} alt={product.name} fetchPriority="high" decoding="async" />
                  <div className={`${styles.stageFact} ${styles.stageFactTop}`}>
                    <span>{copy.high}</span><b>{priceHigh}</b>
                  </div>
                  <div className={`${styles.stageFact} ${styles.stageFactBottom}`}>
                    <span>{copy.low}</span><b>{priceLow}</b>
                  </div>
                  <div className={styles.stageDecision}>
                    <span>{copy.current}</span>
                    <b>{product.brand ? `${product.brand} · ` : ""}{product.name}</b>
                    <ProductJourneyLink href={`/produits/${encodeURIComponent(product.ean)}/`} image={product.image} label={product.name}>{copy.view}</ProductJourneyLink>
                  </div>
                </>
              ) : (
                <div className={styles.stageUnknown}>
                  <span aria-hidden="true">?</span>
                  <p>{copy.unavailableDetail}</p>
                </div>
              )}
            </aside>
          </div>
          <p className={styles.srJourney}>{copy.journeySummary}</p>
        </div>
      </section>

      <section id="home-after-journey" className={styles.proofBand} aria-labelledby="home-proof-title" tabIndex={-1}>
        <div className={styles.proofAtmosphere} aria-hidden="true"><span /><span /><span /></div>
        <div className={`${styles.wrap} ${styles.proofWrap}`}>
          <header className={styles.sectionHead}>
            <span>01</span>
            <div>
              <p className={styles.proofKicker}>{copy.proofKicker}</p>
              <h2 id="home-proof-title">{copy.proofTitle}</h2>
              <p className={styles.proofNote}>{copy.proofNote}</p>
            </div>
          </header>
          {proof ? (
            <dl className={styles.stats}>
              <div><span aria-hidden="true">01</span><dd>{number.format(proof.stats.offers)}</dd><dt>{copy.offers}</dt></div>
              <div><span aria-hidden="true">02</span><dd>{number.format(proof.stats.merchants)}</dd><dt>{copy.merchants}</dt></div>
              <div><span aria-hidden="true">03</span><dd>{number.format(proof.stats.multiMerchant)}</dd><dt>{copy.comparable}</dt></div>
            </dl>
          ) : (
            <UnknownField label={copy.unavailable} detail={copy.unavailableDetail} />
          )}
        </div>
      </section>

      <section className={styles.example} aria-labelledby="home-example-title">
        <div className={styles.exampleAtmosphere} aria-hidden="true" />
        <div className={`${styles.wrap} ${styles.exampleWrap}`}>
          <header className={styles.exampleHead}>
            <span>02</span>
            <p>{copy.exampleEye}</p>
          </header>
          <div className={styles.exampleGrid}>
            <div className={styles.productProof}>
            <DecisionCard
              eyebrow={copy.current}
              titleId="home-example-title"
              title={comparable ? copy.exampleReady : copy.exampleUnknown}
              state={comparable ? "verified" : "unknown"}
              stateLabel={comparable ? copy.verified : copy.unknown}
            >
              {comparable && product ? (
                <>
                  <div className={styles.productIdentity}>
                    <div className={styles.productDetails}>
                      <p className={styles.productName}>{product.brand ? `${product.brand} · ` : ""}{product.name}</p>
                      <ConstraintSummary
                        title={copy.constraints}
                        titleId="home-constraints-title"
                        items={[
                          { label: copy.identity, state: "verified" },
                          { label: copy.current, state: "verified" },
                          { label: copy.scope, state: product.merchants >= 2 ? "verified" : "unknown" },
                        ]}
                      />
                      <ProductJourneyLink className={styles.productLink} href={`/produits/${encodeURIComponent(product.ean)}/`} image={product.image} label={product.name}>{copy.view}</ProductJourneyLink>
                    </div>
                    {product.image ? (
                      <figure className={styles.productVisual}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={product.image} alt="" loading="lazy" decoding="async" />
                      </figure>
                    ) : null}
                  </div>
                </>
              ) : (
                <UnknownField label={copy.unavailable} detail={copy.unavailableDetail} />
              )}
            </DecisionCard>
          </div>
          {comparable && product && priceLow && priceHigh && spread ? (
            <div className={styles.explanation}>
              {observedDate ? <p className={styles.observedAt}>{copy.observed(observedDate)}</p> : null}
              <OfferComparison
                title={copy.compareTitle}
                titleId="home-comparison-title"
                rows={[
                  { label: copy.high, value: priceHigh },
                  { label: copy.low, value: priceLow, emphasis: true },
                  { label: copy.spread, value: spread },
                ]}
              />
              <WhyThisResult title={copy.why} titleId="home-why-title" reasons={copy.reasons(product.ean, product.merchants)} />
            </div>
          ) : null}
          </div>
        </div>
      </section>

      <section className={styles.method} aria-labelledby="home-method-title">
        <div className={styles.wrap}>
          <span className={styles.kicker}>{copy.methodEye}</span>
          <h2 id="home-method-title">{copy.methodTitle}</h2>
          <div className={styles.tradeoffs}>
            {copy.steps.map(([title, body]) => <TradeoffCard key={title} title={title}>{body}</TradeoffCard>)}
          </div>
        </div>
      </section>

      <section className={styles.closing}>
        <div className={styles.wrap}>
          <h2>{copy.closing}</h2>
          <p>{copy.closingBody}</p>
          <div className={styles.closingActions}>
            <a href="/recherche/">{copy.search}</a>
            <a href="/catalogue/">{copy.catalogue}</a>
          </div>
        </div>
      </section>
    </div>
  );
}
