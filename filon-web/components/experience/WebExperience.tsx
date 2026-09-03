"use client";

import { useEffect, useRef, useState } from "react";
import type { Proof } from "@/lib/proof";
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

const COPY = {
  fr: {
    eyebrow: "Copilote d’achat · preuves d’abord",
    titleA: "Comparez le produit exact.",
    titleB: "Voyez ce qui est prouvé.",
    lead: "FILON rapproche les offres comparables de son catalogue, expose leurs sources et laisse les inconnues visibles.",
    searchLabel: "Produit ou besoin à comparer",
    searchPlaceholder: "Ex. casque Sony WH-1000XM5",
    search: "Comparer",
    catalogue: "Explorer le catalogue",
    boundary: "Pas de prix futur inventé. Pas de meilleur choix sans preuve suffisante.",
    proofTitle: "Le périmètre disponible maintenant",
    offers: "offres indexées",
    merchants: "sources marchandes",
    comparable: "produits comparés chez plusieurs marchands",
    exampleEye: "Exemple réel du catalogue",
    exampleReady: "Une comparaison exacte est disponible",
    exampleUnknown: "La comparaison exacte n’est pas disponible",
    verified: "Vérifié",
    unknown: "Inconnu",
    identity: "Identité produit partagée",
    current: "Preuve courante",
    scope: "Périmètre de comparaison",
    high: "Prix le plus élevé observé",
    low: "Prix le plus bas observé",
    spread: "Écart observé",
    compareTitle: "Même produit, même devise",
    why: "Pourquoi cette comparaison apparaît",
    reasons: (ean: string, merchants: number) => [
      `Identifiant produit commun : ${ean}.`,
      `${merchants} marchands distincts dans le périmètre observé.`,
      "Prix courants rapprochés dans une devise explicitement supportée.",
    ],
    view: "Ouvrir le dossier produit",
    unavailable: "Les données live ne permettent pas d’afficher un exemple comparable.",
    unavailableDetail: "FILON conserve l’inconnue au lieu d’inventer un produit ou un prix.",
    methodEye: "Une décision lisible en trois contrôles",
    methodTitle: "L’interface suit la preuve, pas l’inverse.",
    steps: [
      ["Identifier", "Les offres restent séparées si l’identité exacte n’est pas suffisamment établie."],
      ["Vérifier", "Prix, devise, disponibilité, fraîcheur et source sont contrôlés avant affichage favorable."],
      ["Expliquer", "Le résultat montre son périmètre et ce qui manque encore avant toute décision."],
    ],
    constraints: "Ce que l’accueil exige",
    closing: "Commencez par le produit, pas par une promesse.",
    closingBody: "Décrivez votre besoin ou ouvrez le catalogue. FILON s’abstient lorsque le contexte disponible ne suffit pas.",
    skipJourney: "Passer l’expérience",
    journey: [
      "Le marché arrive en fragments.",
      "Une identité exacte survit au bruit.",
      "Les offres deviennent comparables.",
      "La complexité se réduit à une décision.",
    ],
    journeyUnknown: [
      "Le marché arrive en fragments.",
      "L’identité reste à démontrer.",
      "Les offres ne sont pas comparables.",
      "FILON conserve l’inconnue.",
    ],
    journeySummary: "Le parcours montre le marché, l’identité produit, la comparaison et la décision. La recherche reste disponible pendant toute l’expérience.",
  },
  nl: {
    eyebrow: "Aankoopcopiloot · bewijs eerst",
    titleA: "Vergelijk het exacte product.",
    titleB: "Zie wat bewezen is.",
    lead: "FILON koppelt vergelijkbare aanbiedingen uit zijn catalogus, toont hun bronnen en houdt onbekenden zichtbaar.",
    searchLabel: "Product of behoefte om te vergelijken",
    searchPlaceholder: "Bijv. Sony WH-1000XM5 hoofdtelefoon",
    search: "Vergelijken",
    catalogue: "Catalogus verkennen",
    boundary: "Geen verzonnen toekomstige prijs. Geen beste keuze zonder voldoende bewijs.",
    proofTitle: "Het bereik dat nu beschikbaar is",
    offers: "geïndexeerde aanbiedingen",
    merchants: "winkelbronnen",
    comparable: "producten vergeleken bij meerdere winkels",
    exampleEye: "Echt voorbeeld uit de catalogus",
    exampleReady: "Een exacte vergelijking is beschikbaar",
    exampleUnknown: "De exacte vergelijking is niet beschikbaar",
    verified: "Geverifieerd",
    unknown: "Onbekend",
    identity: "Gedeelde productidentiteit",
    current: "Actueel bewijs",
    scope: "Vergelijkingsbereik",
    high: "Hoogste waargenomen prijs",
    low: "Laagste waargenomen prijs",
    spread: "Waargenomen verschil",
    compareTitle: "Hetzelfde product, dezelfde valuta",
    why: "Waarom deze vergelijking verschijnt",
    reasons: (ean: string, merchants: number) => [
      `Gedeelde productidentificatie: ${ean}.`,
      `${merchants} verschillende winkels in het waargenomen bereik.`,
      "Actuele prijzen gekoppeld in een expliciet ondersteunde valuta.",
    ],
    view: "Productdossier openen",
    unavailable: "De livegegevens leveren geen vergelijkbaar voorbeeld op.",
    unavailableDetail: "FILON behoudt het onbekende in plaats van een product of prijs te verzinnen.",
    methodEye: "Een leesbare beslissing in drie controles",
    methodTitle: "De interface volgt het bewijs, niet omgekeerd.",
    steps: [
      ["Identificeren", "Aanbiedingen blijven gescheiden als de exacte identiteit niet voldoende is bewezen."],
      ["Verifiëren", "Prijs, valuta, voorraad, actualiteit en bron worden gecontroleerd vóór een gunstige weergave."],
      ["Uitleggen", "Het resultaat toont zijn bereik en wat nog ontbreekt vóór een beslissing."],
    ],
    constraints: "Wat de startpagina vereist",
    closing: "Begin met het product, niet met een belofte.",
    closingBody: "Beschrijf je behoefte of open de catalogus. FILON onthoudt zich wanneer de beschikbare context niet volstaat.",
    skipJourney: "Ervaring overslaan",
    journey: [
      "De markt komt binnen als fragmenten.",
      "Een exacte identiteit overleeft de ruis.",
      "Aanbiedingen worden vergelijkbaar.",
      "Complexiteit wordt een beslissing.",
    ],
    journeyUnknown: [
      "De markt komt binnen als fragmenten.",
      "De identiteit moet nog worden bewezen.",
      "De aanbiedingen zijn niet vergelijkbaar.",
      "FILON bewaart het onbekende.",
    ],
    journeySummary: "Het traject toont de markt, productidentiteit, vergelijking en beslissing. Zoeken blijft tijdens de hele ervaring beschikbaar.",
  },
  en: {
    eyebrow: "Shopping copilot · evidence first",
    titleA: "Compare the exact product.",
    titleB: "See what is proven.",
    lead: "FILON reconciles comparable catalogue offers, exposes their sources and keeps unknowns visible.",
    searchLabel: "Product or need to compare",
    searchPlaceholder: "E.g. Sony WH-1000XM5 headphones",
    search: "Compare",
    catalogue: "Explore the catalogue",
    boundary: "No invented future price. No best choice without sufficient evidence.",
    proofTitle: "The scope available now",
    offers: "indexed offers",
    merchants: "merchant sources",
    comparable: "products compared across several merchants",
    exampleEye: "Real catalogue example",
    exampleReady: "An exact comparison is available",
    exampleUnknown: "The exact comparison is unavailable",
    verified: "Verified",
    unknown: "Unknown",
    identity: "Shared product identity",
    current: "Current evidence",
    scope: "Comparison scope",
    high: "Highest observed price",
    low: "Lowest observed price",
    spread: "Observed spread",
    compareTitle: "Same product, same currency",
    why: "Why this comparison appears",
    reasons: (ean: string, merchants: number) => [
      `Shared product identifier: ${ean}.`,
      `${merchants} distinct merchants in the observed scope.`,
      "Current prices reconciled in an explicitly supported currency.",
    ],
    view: "Open the product record",
    unavailable: "Live data cannot provide a comparable example.",
    unavailableDetail: "FILON preserves the unknown instead of inventing a product or price.",
    methodEye: "A readable decision in three checks",
    methodTitle: "The interface follows the evidence, not the other way round.",
    steps: [
      ["Identify", "Offers remain separate when exact identity is not sufficiently established."],
      ["Verify", "Price, currency, availability, freshness and source are checked before a favourable display."],
      ["Explain", "The result exposes its scope and what is still missing before a decision."],
    ],
    constraints: "What the homepage requires",
    closing: "Start with the product, not a promise.",
    closingBody: "Describe your need or open the catalogue. FILON abstains when the available context is insufficient.",
    skipJourney: "Skip the experience",
    journey: [
      "The market arrives in fragments.",
      "An exact identity survives the noise.",
      "Offers become comparable.",
      "Complexity resolves into a decision.",
    ],
    journeyUnknown: [
      "The market arrives in fragments.",
      "Identity remains unproven.",
      "The offers are not comparable.",
      "FILON preserves the unknown.",
    ],
    journeySummary: "The journey reveals market, product identity, comparison and decision. Search remains available throughout the experience.",
  },
} as const;

const NUMBER_LOCALE = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

export function WebExperience({ proof }: { proof: Proof | null }) {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const journeyRef = useRef<HTMLElement | null>(null);
  const [journeyShot, setJourneyShot] = useState(0);
  const [reducedJourney, setReducedJourney] = useState(false);
  const product = proof?.product ?? null;
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, locale) : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, locale) : null;
  const spread = product ? formatSupportedMoney(product.priceMax - product.priceMin, product.currency, locale) : null;
  const comparable = Boolean(product && priceLow && priceHigh && spread);
  const journeyLines = comparable ? copy.journey : copy.journeyUnknown;
  const number = new Intl.NumberFormat(NUMBER_LOCALE[locale]);

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
        return;
      }
      const root = journeyRef.current;
      if (!root) return;
      const rect = root.getBoundingClientRect();
      const distance = Math.max(1, root.offsetHeight - window.innerHeight);
      const progress = Math.max(0, Math.min(1, -rect.top / distance));
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

  return (
    <div className={`${styles.page} p11-web-experience`}>
      <section ref={journeyRef} className={styles.hero} aria-labelledby="p11-home-title" data-immersive-journey data-reduced={reducedJourney}>
        <a className={styles.skipJourney} href="#p19-home-after-journey">{copy.skipJourney}</a>
        <div className={styles.heroSticky} data-shot={journeyShot}>
          <div className={styles.heroGlow} aria-hidden="true" />
          <div className={`${styles.wrap} ${styles.heroGrid}`}>
            <div className={styles.heroCopy}>
              <div className={styles.planMarker} aria-hidden="true">FILON / PLAN {String(journeyShot + 1).padStart(2, "0")}</div>
              <EvidenceBadge state="verified">{copy.eyebrow}</EvidenceBadge>
              <h1 id="p11-home-title"><span>{copy.titleA}</span>{copy.titleB}</h1>
              <div className={styles.journeyCopy} aria-hidden="true">
                {journeyLines.map((line, index) => <p key={line} data-active={journeyShot === index}>{line}</p>)}
              </div>
              <p className={styles.lead}>{copy.lead}</p>
              <form className={styles.search} action="/recherche/" method="get" role="search">
                <label htmlFor="p11-query">{copy.searchLabel}</label>
                <div>
                  <input id="p11-query" type="search" name="q" minLength={2} placeholder={copy.searchPlaceholder} autoComplete="off" />
                  <button type="submit">{copy.search}</button>
                </div>
              </form>
              <div className={styles.actions}>
                <a href="/catalogue/">{copy.catalogue}</a>
                <p>{copy.boundary}</p>
              </div>
            </div>
            <aside className={styles.heroStage} aria-label={copy.exampleEye}>
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
                    <a href={`/produits/${encodeURIComponent(product.ean)}/`}>{copy.view}</a>
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
          <div className={styles.shotRail} aria-hidden="true">
            {["CHAOS", "IDENTITÉ", "MARCHÉ", "DÉCISION"].map((label, index) => <span key={label} data-active={journeyShot === index}>{label}</span>)}
          </div>
          <p className={styles.srJourney}>{copy.journeySummary}</p>
        </div>
      </section>

      <section id="p19-home-after-journey" className={styles.proofBand} aria-labelledby="p11-proof-title">
        <div className={styles.wrap}>
          <header className={styles.sectionHead}>
            <span>01</span>
            <h2 id="p11-proof-title">{copy.proofTitle}</h2>
          </header>
          {proof ? (
            <dl className={styles.stats}>
              <div><dt>{copy.offers}</dt><dd>{number.format(proof.stats.offers)}</dd></div>
              <div><dt>{copy.merchants}</dt><dd>{number.format(proof.stats.merchants)}</dd></div>
              <div><dt>{copy.comparable}</dt><dd>{number.format(proof.stats.multiMerchant)}</dd></div>
            </dl>
          ) : (
            <UnknownField label={copy.unavailable} detail={copy.unavailableDetail} />
          )}
        </div>
      </section>

      <section className={styles.example} aria-labelledby="p11-example-title">
        <div className={`${styles.wrap} ${styles.exampleGrid}`}>
          <div>
            <span className={styles.kicker}>{copy.exampleEye}</span>
            <DecisionCard
              eyebrow={copy.current}
              titleId="p11-example-title"
              title={comparable ? copy.exampleReady : copy.exampleUnknown}
              state={comparable ? "verified" : "unknown"}
              stateLabel={comparable ? copy.verified : copy.unknown}
            >
              {comparable && product ? (
                <>
                  <p className={styles.productName}>{product.brand ? `${product.brand} · ` : ""}{product.name}</p>
                  <ConstraintSummary
                    title={copy.constraints}
                    titleId="p11-constraints-title"
                    items={[
                      { label: copy.identity, state: "verified" },
                      { label: copy.current, state: "verified" },
                      { label: copy.scope, state: product.merchants >= 2 ? "verified" : "unknown" },
                    ]}
                  />
                  <a className={styles.productLink} href={`/produits/${encodeURIComponent(product.ean)}/`}>{copy.view}</a>
                </>
              ) : (
                <UnknownField label={copy.unavailable} detail={copy.unavailableDetail} />
              )}
            </DecisionCard>
          </div>
          {comparable && product && priceLow && priceHigh && spread ? (
            <div className={styles.explanation}>
              <OfferComparison
                title={copy.compareTitle}
                titleId="p11-comparison-title"
                rows={[
                  { label: copy.high, value: priceHigh },
                  { label: copy.low, value: priceLow, emphasis: true },
                  { label: copy.spread, value: spread },
                ]}
              />
              <WhyThisResult title={copy.why} titleId="p11-why-title" reasons={copy.reasons(product.ean, product.merchants)} />
            </div>
          ) : null}
        </div>
      </section>

      <section className={styles.method} aria-labelledby="p11-method-title">
        <div className={styles.wrap}>
          <span className={styles.kicker}>{copy.methodEye}</span>
          <h2 id="p11-method-title">{copy.methodTitle}</h2>
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
