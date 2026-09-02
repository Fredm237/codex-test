"use client";

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
  },
} as const;

const NUMBER_LOCALE = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

export function WebExperience({ proof }: { proof: Proof | null }) {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const product = proof?.product ?? null;
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, locale) : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, locale) : null;
  const spread = product ? formatSupportedMoney(product.priceMax - product.priceMin, product.currency, locale) : null;
  const comparable = Boolean(product && priceLow && priceHigh && spread);
  const number = new Intl.NumberFormat(NUMBER_LOCALE[locale]);

  return (
    <div className={`${styles.page} p11-web-experience`}>
      <section className={styles.hero} aria-labelledby="p11-home-title">
        <div className={styles.heroGlow} aria-hidden="true" />
        <div className={`${styles.wrap} ${styles.heroGrid}`}>
          <div className={styles.heroCopy}>
            <EvidenceBadge state="verified">{copy.eyebrow}</EvidenceBadge>
            <h1 id="p11-home-title"><span>{copy.titleA}</span>{copy.titleB}</h1>
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
            <span className={styles.stageIndex}>FILON / 01</span>
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
                <a href={`/produits/${encodeURIComponent(product.ean)}/`} aria-label={`${copy.view} — ${product.name}`} />
              </>
            ) : (
              <div className={styles.stageUnknown}>
                <span aria-hidden="true">?</span>
                <p>{copy.unavailableDetail}</p>
              </div>
            )}
          </aside>
        </div>
      </section>

      <section className={styles.proofBand} aria-labelledby="p11-proof-title">
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
