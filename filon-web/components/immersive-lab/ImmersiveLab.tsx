"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { formatSupportedMoney } from "@/lib/currency";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import type { Proof } from "@/lib/proof";
import { ProductJourneyLink } from "@/components/experience/ProductJourneyLink";
import { SkipLink } from "@/components/editorial/SkipLink";
import { SignatureMomentGate } from "./SignatureMomentGate";
import styles from "./immersive-lab.module.css";

type Direction = "focus" | "table" | "relief";

const DIRECTIONS: Array<{ id: Direction; code: string; name: string; promise: string }> = [
  { id: "focus", code: "A", name: "Mise au point", promise: "L'incompatible se brouille. La preuve devient nette." },
  { id: "table", code: "B", name: "Table des preuves", promise: "Les faits s'assemblent autour du produit exact." },
  { id: "relief", code: "C", name: "Relief de décision", promise: "Le paysage des prix se transforme en plan lisible." },
];

const DURATION_MS = 12_000;

type LabMetrics = {
  lcp: number | null;
  cls: number;
  inp: number | null;
  longestTask: number;
  immersiveLongestTask: number | null;
  transferKb: number;
  resources: number;
  lcpElement: string | null;
  largestResource: string | null;
  largestResourceKb: number;
};

function useReducedExperience() {
  const [reduced, setReduced] = useState(true);

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
    const update = () => setReduced(
      motion.matches || Boolean(connection?.saveData) || connection?.effectiveType === "slow-2g" || connection?.effectiveType === "2g",
    );
    update();
    motion.addEventListener("change", update);
    return () => motion.removeEventListener("change", update);
  }, []);

  return reduced;
}

function LabTelemetry() {
  const [metrics, setMetrics] = useState<LabMetrics | null>(null);

  useEffect(() => {
    let lcp: number | null = null;
    let lcpElement: string | null = null;
    let cls = 0;
    let inp: number | null = null;
    let longestTask = 0;
    const observers: PerformanceObserver[] = [];

    const observe = (type: string, onEntries: (entries: PerformanceEntry[]) => void, options: PerformanceObserverInit = { type, buffered: true }) => {
      try {
        const observer = new PerformanceObserver((list) => onEntries(list.getEntries()));
        observer.observe(options);
        observers.push(observer);
      } catch {
        // Une métrique absente reste inconnue : aucun score de secours.
      }
    };

    observe("largest-contentful-paint", (entries) => {
      const last = entries.at(-1) as (PerformanceEntry & { element?: Element | null }) | undefined;
      if (last) {
        lcp = last.startTime;
        lcpElement = last.element
          ? `${last.element.tagName.toLowerCase()}${last.element.id ? `#${last.element.id}` : ""}`
          : null;
      }
    });
    observe("layout-shift", (entries) => {
      for (const entry of entries as Array<PerformanceEntry & { hadRecentInput?: boolean; value?: number }>) {
        if (!entry.hadRecentInput && Number.isFinite(entry.value)) cls += entry.value ?? 0;
      }
    });
    observe("longtask", (entries) => {
      for (const entry of entries) longestTask = Math.max(longestTask, entry.duration);
    });
    observe("event", (entries) => {
      for (const entry of entries) inp = Math.max(inp ?? 0, entry.duration);
    }, { type: "event", buffered: true, durationThreshold: 40 } as PerformanceObserverInit);

    const sample = () => {
      const resources = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
      const immersiveStart = performance.getEntriesByName("filon-immersive-init-start").at(-1);
      const immersiveReady = performance.getEntriesByName("filon-immersive-init-ready").at(-1);
      const immersiveLongestTask = immersiveStart && immersiveReady
        ? Math.max(0, ...performance.getEntriesByType("longtask")
          .filter((entry) => entry.startTime >= immersiveStart.startTime && entry.startTime <= immersiveReady.startTime)
          .map((entry) => entry.duration))
        : null;
      const largest = [...resources].sort((a, b) => (b.transferSize || 0) - (a.transferSize || 0))[0];
      setMetrics({
        lcp: lcp === null ? null : Math.round(lcp),
        cls: Number(cls.toFixed(4)),
        inp: inp === null ? null : Math.round(inp),
        longestTask: Math.round(longestTask),
        immersiveLongestTask: immersiveLongestTask === null ? null : Math.round(immersiveLongestTask),
        transferKb: Math.round(resources.reduce((total, entry) => total + (entry.transferSize || 0), 0) / 1024),
        resources: resources.length,
        lcpElement,
        largestResource: largest ? largest.name.split("?")[0].split("/").at(-1) ?? null : null,
        largestResourceKb: Math.round((largest?.transferSize || 0) / 1024),
      });
    };

    const firstSample = window.setTimeout(sample, 2_600);
    const interval = window.setInterval(sample, 1_500);
    return () => {
      window.clearTimeout(firstSample);
      window.clearInterval(interval);
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  const value = (metric: number | null | undefined, suffix: string) => metric === null || metric === undefined ? "non mesuré" : `${metric}${suffix}`;
  return (
    <section className={styles.telemetry} aria-labelledby="lab-telemetry-title">
      <div>
        <p className={styles.eyebrow}>SONDE LOCALE / ROUTE LABORATOIRE</p>
        <h2 id="lab-telemetry-title">Mesurer avant de raccorder.</h2>
        <p>Ces valeurs décrivent ce chargement, pas la production. Une métrique indisponible reste explicitement non mesurée.</p>
      </div>
      <dl
        data-lab-metrics-ready={metrics !== null}
        data-lcp-element={metrics?.lcpElement ?? "unknown"}
        data-largest-resource={metrics?.largestResource ?? "unknown"}
        data-largest-resource-kb={metrics?.largestResourceKb ?? 0}
      >
        <div><dt>LCP</dt><dd data-metric="lcp">{value(metrics?.lcp, " ms")}</dd></div>
        <div><dt>CLS</dt><dd data-metric="cls">{metrics ? metrics.cls : "non mesuré"}</dd></div>
        <div><dt>Interaction</dt><dd data-metric="inp">{value(metrics?.inp, " ms")}</dd></div>
        <div><dt>Tâche longue max.</dt><dd data-metric="longtask">{value(metrics?.longestTask, " ms")}</dd></div>
        <div><dt>Initialisation immersive</dt><dd data-metric="immersive-longtask">{value(metrics?.immersiveLongestTask, " ms")}</dd></div>
        <div><dt>Transfert observé</dt><dd data-metric="transfer">{value(metrics?.transferKb, " Ko")}</dd></div>
        <div><dt>Ressources</dt><dd data-metric="resources">{value(metrics?.resources, "")}</dd></div>
      </dl>
    </section>
  );
}

function ProductSubject({ product }: { product: ImmersiveExactProductProof | null }) {
  return (
    <div className={styles.subject}>
      {product?.image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={product.image} alt="" decoding="async" loading="lazy" fetchPriority="low" />
      ) : (
        <span className={styles.unknownGlyph} aria-hidden="true">?</span>
      )}
    </div>
  );
}

function CinematicJourney({ product, reduced }: { product: ImmersiveExactProductProof | null; reduced: boolean }) {
  const rootRef = useRef<HTMLElement | null>(null);
  const [progress, setProgress] = useState(reduced ? 1 : 0);

  useEffect(() => {
    if (reduced) {
      setProgress(1);
      return;
    }
    let frame = 0;
    const update = () => {
      frame = 0;
      const root = rootRef.current;
      if (!root) return;
      const rect = root.getBoundingClientRect();
      const distance = Math.max(1, root.offsetHeight - window.innerHeight);
      setProgress(Math.max(0, Math.min(1, -rect.top / distance)));
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [reduced]);

  const shot = progress < .22 ? 0 : progress < .46 ? 1 : progress < .72 ? 2 : 3;
  const copy = [
    "Le marché arrive en fragments.",
    "Une identité exacte survit au bruit.",
    "Les offres deviennent comparables.",
    "La complexité se réduit à une décision.",
  ][shot];
  const low = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;

  return (
    <section ref={rootRef} className={styles.journey} aria-labelledby="lab-journey-title">
      <SkipLink className={styles.skipJourney} targetId="p19-lab-after-journey">
        Passer l’expérience
      </SkipLink>
      <div className={styles.journeySticky} style={{ "--journey": progress } as CSSProperties} data-shot={shot}>
        <div className={styles.journeyText}>
          <span>FILON / PLAN {String(shot + 1).padStart(2, "0")}</span>
          <h2 id="lab-journey-title">{copy}</h2>
        </div>
        <div className={styles.chaosField} aria-hidden="true">
          {(product?.offers ?? []).slice(0, 5).map((offer, index) => (
            <span key={offer.id} style={{ "--fragment": index } as CSSProperties}>
              {offer.merchant}<b>{formatSupportedMoney(offer.price, offer.currency, "fr") ?? "?"}</b>
            </span>
          ))}
          {!product ? <span>PREUVE INSUFFISANTE<b>?</b></span> : null}
        </div>
        <div className={styles.continuityObject} aria-hidden="true">
          {product?.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image} alt="" decoding="async" loading="lazy" fetchPriority="low" />
          ) : <span>?</span>}
        </div>
        <div className={styles.marketRings} aria-hidden="true"><i /><i /><i /></div>
        <div className={styles.journeyDecision}>
          <span>{product ? "PREUVE COURANTE" : "ABSTENTION"}</span>
          <h3>{product ? [product.brand, product.name].filter(Boolean).join(" · ") : "Produit non démontré"}</h3>
          <p>{product && low ? `${low} · ${product.merchants} marchands comparables` : "FILON ne fabrique ni identité, ni prix."}</p>
          {product ? (
            <ProductJourneyLink href={`/produits/${encodeURIComponent(product.ean)}`} image={product.image} label={product.name}>Entrer dans la preuve</ProductJourneyLink>
          ) : <a href="/recherche/">Lancer une recherche</a>}
        </div>
        <div className={styles.shotRail} aria-hidden="true">
          {["CHAOS", "IDENTITÉ", "MARCHÉ", "DÉCISION"].map((label, index) => <span key={label} data-active={shot === index}>{label}</span>)}
        </div>
        <p className={styles.srJourney}>Le parcours montre successivement le chaos marchand, la résolution d’identité, la comparaison des offres et la décision. La même preuve produit reste disponible dans le document.</p>
      </div>
    </section>
  );
}

function FocusScene({ product }: { product: ImmersiveExactProductProof | null }) {
  return (
    <div className={`${styles.world} ${styles.focusWorld}`} aria-hidden="true">
      <div className={styles.focusGlow} />
      <div className={`${styles.lens} ${styles.lensOne}`} />
      <div className={`${styles.lens} ${styles.lensTwo}`} />
      <ProductSubject product={product} />
      <span className={`${styles.fragment} ${styles.fragmentA}`}>source ≠ preuve</span>
      <span className={`${styles.fragment} ${styles.fragmentB}`}>devise ?</span>
      <span className={`${styles.fragment} ${styles.fragmentC}`}>stock ?</span>
      <span className={`${styles.fragment} ${styles.fragmentD}`}>fraîcheur ?</span>
    </div>
  );
}

function TableScene({ product, priceLow, priceHigh }: { product: ImmersiveExactProductProof | null; priceLow: string | null; priceHigh: string | null }) {
  return (
    <div className={`${styles.world} ${styles.tableWorld}`} aria-hidden="true">
      <div className={styles.tablePlane} />
      <ProductSubject product={product} />
      <div className={`${styles.evidenceCard} ${styles.cardIdentity}`}><span>01</span><b>IDENTITÉ</b><small>{product ? "exacte" : "inconnue"}</small></div>
      <div className={`${styles.evidenceCard} ${styles.cardLow}`}><span>02</span><b>PRIX BAS</b><small>{priceLow ?? "inconnu"}</small></div>
      <div className={`${styles.evidenceCard} ${styles.cardHigh}`}><span>03</span><b>PRIX HAUT</b><small>{priceHigh ?? "inconnu"}</small></div>
      <div className={`${styles.evidenceCard} ${styles.cardFresh}`}><span>04</span><b>PREUVE</b><small>{product ? "courante" : "insuffisante"}</small></div>
    </div>
  );
}

function ReliefScene({ product }: { product: ImmersiveExactProductProof | null }) {
  return (
    <div className={`${styles.world} ${styles.reliefWorld}`} aria-hidden="true">
      <div className={styles.sun} />
      <div className={styles.terrain}>
        {Array.from({ length: 9 }, (_, index) => <span key={index} style={{ "--line": index } as CSSProperties} />)}
      </div>
      <div className={styles.reliefProduct}><ProductSubject product={product} /></div>
      <span className={styles.axisStart}>OFFRES</span>
      <span className={styles.axisEnd}>DÉCISION</span>
    </div>
  );
}

function formatObservation(value: string): string {
  try {
    return new Intl.DateTimeFormat("fr-BE", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Europe/Brussels",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function ExactProductPrototype({ product }: { product: ImmersiveExactProductProof | null }) {
  const [step, setStep] = useState(0);
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, "fr") : null;

  return (
    <section className={styles.exactPrototype} aria-labelledby="lab-exact-title">
      <div className={styles.sectionHeading}>
        <p className={styles.eyebrow}>P19C + P19D / RECHERCHE → PRODUIT EXACT</p>
        <h2 id="lab-exact-title">Une transition qui ne perd jamais la provenance.</h2>
        <p>Les trois étapes partagent la même preuve serveur. Le mouvement change sa lecture, jamais son contenu.</p>
      </div>

      <div className={styles.stepControls} role="group" aria-label="Étapes du prototype produit exact">
        {["01 · Signal", "02 · Résolution", "03 · Comparaison"].map((label, index) => (
          <button key={label} type="button" className={step === index ? styles.activeStep : ""} aria-pressed={step === index} onClick={() => setStep(index)}>{label}</button>
        ))}
      </div>

      <div className={styles.exactStage} data-step={step}>
        <div className={styles.querySignal}>
          <span>REQUÊTE STRUCTURÉE</span>
          <strong>{product ? [product.brand, product.name].filter(Boolean).join(" ") : "Produit non prouvé"}</strong>
          <small>{product?.category ?? "catégorie inconnue"}</small>
        </div>
        <div className={styles.identityNode}>
          {product?.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image} alt={product.name} decoding="async" loading="lazy" fetchPriority="low" />
          ) : <span aria-hidden="true">?</span>}
          <div><small>EAN</small><b>{product?.ean ?? "inconnu"}</b></div>
        </div>
        <div className={styles.offerOrbit} aria-hidden="true">
          {(product?.offers ?? []).slice(0, 5).map((offer, index) => <i key={offer.id} style={{ "--offer": index } as CSSProperties} />)}
        </div>
        <div className={styles.comparisonNode}>
          <span>{product ? "COMPARAISON COURANTE" : "ABSTENTION"}</span>
          <strong>{priceLow && priceHigh ? `${priceLow} — ${priceHigh}` : "Prix non démontré"}</strong>
          <small>{product ? `${product.offers.length} offres · ${product.merchants} marchands` : "Preuve insuffisante"}</small>
        </div>
      </div>

      {product ? (
        <div className={styles.exactEvidence}>
          <article>
            <span>IDENTITÉ RÉSOLUE</span>
            <h3>{[product.brand, product.name].filter(Boolean).join(" · ")}</h3>
            <dl>
              <div><dt>EAN</dt><dd>{product.ean}</dd></div>
              <div><dt>Dernière preuve</dt><dd>{formatObservation(product.latestObservedAt)}</dd></div>
              <div><dt>Historique</dt><dd>{product.historyHeadline ?? "Non documenté"}</dd></div>
              <div><dt>Échantillons</dt><dd>{product.historySamples ?? "inconnu"}</dd></div>
            </dl>
          </article>
          <div className={styles.offerList}>
            <div className={styles.offerHeader}><span>Source marchande</span><span>Observation</span><span>Prix</span></div>
            {product.offers.map((offer) => (
              <div className={styles.offerRow} key={offer.id}>
                <span><b>{offer.merchant}</b><small>{offer.region ?? "région inconnue"}</small></span>
                <time dateTime={offer.observedAt}>{formatObservation(offer.observedAt)}</time>
                <strong>{formatSupportedMoney(offer.price, offer.currency, "fr") ?? "inconnu"}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className={styles.failClosed}>Aucune fiche n’a franchi simultanément les gates identité, devise, fraîcheur et pluralité marchande. Le prototype s’abstient.</p>
      )}
    </section>
  );
}

function MobilePrototype({ product }: { product: ImmersiveExactProductProof | null }) {
  const [state, setState] = useState(0);
  const low = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;

  return (
    <section className={styles.mobilePrototype} aria-labelledby="lab-mobile-title">
      <div className={styles.mobileCopy}>
        <p className={styles.eyebrow}>P19E / MOBILE AUTONOME</p>
        <h2 id="lab-mobile-title">Trois états. Une seule transition structurante.</h2>
        <p>Le mobile ne recadre pas la scène desktop. Il condense signal, preuve et action dans une lecture verticale utilisable au pouce.</p>
        <div className={styles.mobileStates} role="group" aria-label="États du storyboard mobile">
          {["Signal", "Preuve", "Action"].map((label, index) => <button key={label} type="button" aria-pressed={state === index} onClick={() => setState(index)}>{index + 1}. {label}</button>)}
        </div>
      </div>
      <div className={styles.phone} data-mobile-state={state}>
        <div className={styles.phoneTop}><span>FILON</span><small>PREUVE ACTIVE</small></div>
        <div className={styles.mobileSignal}>
          <small>PRODUIT EXACT</small>
          <h3>{product ? [product.brand, product.name].filter(Boolean).join(" ") : "Identité non démontrée"}</h3>
        </div>
        <div className={styles.mobileProof}>
          {product?.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image} alt="" decoding="async" loading="lazy" fetchPriority="low" />
          ) : <span aria-hidden="true">?</span>}
          <div><small>À PARTIR DE</small><strong>{low ?? "inconnu"}</strong><p>{product ? `${product.merchants} marchands · preuve courante` : "FILON s’abstient"}</p></div>
        </div>
        {product ? (
          <ProductJourneyLink className={styles.mobileAction} href={`/produits/${encodeURIComponent(product.ean)}`} image={product.image} label={product.name}>Voir toutes les preuves</ProductJourneyLink>
        ) : <a className={styles.mobileAction} href="/recherche/">Rechercher un produit</a>}
        <div className={styles.phoneProgress} aria-hidden="true"><span /><span /><span /></div>
      </div>
    </section>
  );
}

export function ImmersiveLab({ proof, exactProduct }: { proof: Proof | null; exactProduct: ImmersiveExactProductProof | null }) {
  const reduced = useReducedExperience();
  const [direction, setDirection] = useState<Direction>("table");
  const [progress, setProgress] = useState(1);
  const [playing, setPlaying] = useState(false);
  const frameRef = useRef(0);
  const startedAtRef = useRef(0);
  const product = exactProduct;
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, "fr") : null;
  const selected = useMemo(() => DIRECTIONS.find((item) => item.id === direction) ?? DIRECTIONS[1], [direction]);

  const stop = useCallback(() => {
    cancelAnimationFrame(frameRef.current);
    setPlaying(false);
  }, []);

  const tick = useCallback((now: number) => {
    const next = Math.min(1, (now - startedAtRef.current) / DURATION_MS);
    setProgress(next);
    if (next < 1) frameRef.current = requestAnimationFrame(tick);
    else setPlaying(false);
  }, []);

  const play = useCallback(() => {
    cancelAnimationFrame(frameRef.current);
    if (reduced) {
      setProgress(1);
      return;
    }
    setProgress(0);
    setPlaying(true);
    startedAtRef.current = performance.now();
    frameRef.current = requestAnimationFrame(tick);
  }, [reduced, tick]);

  useEffect(() => () => cancelAnimationFrame(frameRef.current), []);
  useEffect(() => {
    if (reduced) {
      cancelAnimationFrame(frameRef.current);
      setPlaying(false);
      setProgress(1);
    }
  }, [reduced]);

  const choose = (next: Direction) => {
    stop();
    setDirection(next);
    setProgress(1);
  };

  const stageStyle = { "--p": progress } as CSSProperties;
  const productName = product ? `${product.brand ? `${product.brand} · ` : ""}${product.name}` : "Produit comparable non disponible";

  return (
    <div className={`${styles.page} p19-immersive-lab`}>
      <header className={styles.intro}>
        <p className={styles.eyebrow}>FILON / LABORATOIRE IMMERSIF / P19</p>
        <h1>Le chaos marchand<br /><em>devient une décision.</em></h1>
        <p className={styles.lead}>Quatre moments signature transforment le marché en espace physique sans modifier l'accueil public. La preuve reste dans le DOM ; la profondeur ne fait que l'expliquer.</p>
      </header>

      <CinematicJourney product={product} reduced={reduced} />

      <SignatureMomentGate product={product} reduced={reduced} />

      <section id="p19-lab-after-journey" className={styles.prototype} aria-labelledby="lab-direction-title" tabIndex={-1}>
        <div className={styles.controls}>
          <div>
            <span className={styles.controlLabel}>Direction créative</span>
            <h2 id="lab-direction-title">{selected.code} — {selected.name}</h2>
          </div>
          <div className={styles.directionTabs} role="group" aria-label="Choisir une direction créative">
            {DIRECTIONS.map((item) => (
              <button key={item.id} type="button" className={direction === item.id ? styles.active : ""} aria-pressed={direction === item.id} onClick={() => choose(item.id)}>
                <span>{item.code}</span>{item.name}
              </button>
            ))}
          </div>
        </div>

        <div className={`${styles.stage} ${styles[direction]}`} style={stageStyle} aria-describedby="lab-scene-description">
          {direction === "focus" ? <FocusScene product={product} /> : null}
          {direction === "table" ? <TableScene product={product} priceLow={priceLow} priceHigh={priceHigh} /> : null}
          {direction === "relief" ? <ReliefScene product={product} /> : null}
          <div className={styles.narrative}>
            <span>FILON / {selected.code}</span>
            <p>{progress < .28 ? "Des offres. Pas encore une comparaison." : progress < .7 ? "FILON écarte ce qui ne peut pas être prouvé." : selected.promise}</p>
          </div>
          <div className={styles.decision}>
            <span>{product ? "PREUVE COURANTE" : "ÉTAT FAIL-CLOSED"}</span>
            <h3>{productName}</h3>
            {product && priceLow && priceHigh ? (
              <dl><div><dt>Plage observée</dt><dd>{priceLow} — {priceHigh}</dd></div><div><dt>Marchands</dt><dd>{product.merchants}</dd></div></dl>
            ) : (
              <p>FILON conserve l'inconnue au lieu d'inventer un produit ou un prix.</p>
            )}
            <a href="/recherche/">Commencer une recherche</a>
          </div>
        </div>

        <div className={styles.transport}>
          <button type="button" onClick={playing ? stop : play} disabled={reduced}>
            {reduced ? "Mouvement réduit · état final" : playing ? "Mettre en pause" : "Rejouer 12 secondes"}
          </button>
          <label>
            <span>Progression du prototype</span>
            <input type="range" min="0" max="100" value={Math.round(progress * 100)} onChange={(event) => { stop(); setProgress(Number(event.target.value) / 100); }} aria-valuetext={`${Math.round(progress * 100)} %`} />
          </label>
        </div>
        <p id="lab-scene-description" className={styles.description}>{selected.promise} Le résultat textuel et l'action restent accessibles, même lorsque le mouvement est désactivé.</p>
      </section>

      <ExactProductPrototype product={product} />
      <MobilePrototype product={product} />
      <LabTelemetry />

      <section className={styles.boundaries} aria-labelledby="lab-boundaries-title">
        <p className={styles.eyebrow}>FRONTIÈRES DE PRODUCTION</p>
        <h2 id="lab-boundaries-title">Le spectacle ne peut jamais dépasser la preuve.</h2>
        <div>
          <article><span>01</span><h3>DOM d'abord</h3><p>Texte, prix, provenance, focus et actions restent lisibles sans rendu immersif. {proof ? `${proof.stats.offers.toLocaleString("fr-BE")} offres sont agrégées par l'API.` : "Les agrégats restent inconnus si l'API est indisponible."}</p></article>
          <article><span>02</span><h3>Unknown intact</h3><p>Une donnée incomplète ne reçoit ni prix de secours, ni objet synthétique, ni signal favorable.</p></article>
          <article><span>03</span><h3>Coût borné</h3><p>Cette route de laboratoire n'est ni indexée ni raccordée à la home. Les anciens 1 200 frames ne sont pas chargés.</p></article>
        </div>
      </section>
    </div>
  );
}
