"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { API } from "@/lib/api";
import { useLocale, type Locale } from "@/lib/i18n";
import "./outfit-studio.css";

type Mode = "create" | "complete" | "recreate" | "optimize" | "compare" | "discover";
type FeatureState = "loading" | "ready" | "disabled" | "unavailable";

type OutfitItem = {
  offer_id: number;
  name: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  availability: "in_stock" | "out_of_stock" | "unknown";
  image_url: string | null;
  deep_link: string | null;
  role: "base" | "footwear" | "accessory";
  merchant: { name: string; region: string | null };
};

type OutfitSolution = {
  decision: "recommend" | "abstain";
  style_score: number | null;
  confidence_score: number;
  confidence_band: "high" | "medium" | "low";
  total_known_price: { amount: number; currency: string; scope: "items_only" } | null;
  delivery: "unknown";
  items: OutfitItem[];
  rationale_keys: string[];
  unknowns: string[];
  rejection_reason: string | null;
};

type OutfitResponse = {
  trace_id: string;
  candidates_considered: number;
  solution: OutfitSolution;
};

type Copy = {
  eyebrow: string;
  title: string;
  intro: string;
  modeLabel: string;
  prompt: string;
  placeholder: string;
  examples: string[];
  submit: string;
  thinking: string;
  disabledTitle: string;
  disabledBody: string;
  unavailable: string;
  resultEyebrow: string;
  knownTotal: string;
  delivery: string;
  confidence: string;
  style: string;
  why: string;
  unknowns: string;
  noSolution: string;
  candidates: string;
  viewOffer: string;
  inStock: string;
  availabilityUnknown: string;
  feedbackQuestion: string;
  keep: string;
  reject: string;
  feedbackThanks: string;
  roles: Record<OutfitItem["role"], string>;
  modes: Record<Mode, { label: string; hint: string }>;
};

const COPY: Record<Locale, Copy> = {
  fr: {
    eyebrow: "FILON Intelligence · Fashion Expert",
    title: "Outfit Studio",
    intro: "Décrivez une intention. FILON compose une solution avec des offres réelles, puis vous dit clairement ce qu’il sait et ce qui reste à vérifier.",
    modeLabel: "Que voulez-vous faire ?",
    prompt: "Décrivez votre besoin",
    placeholder: "Ex. Une robe de mariage sous 200 €, avec chaussures.",
    examples: ["Un look de mariage sous 200 €", "Compléter une tenue de travail", "Une robe avec chaussures pour une soirée"],
    submit: "Construire une solution",
    thinking: "FILON vérifie les pièces réelles du catalogue…",
    disabledTitle: "Outfit Studio arrive bientôt",
    disabledBody: "Le module est isolé du catalogue et n’est pas encore activé publiquement. FILON ne crée pas de recommandation de style sans offres vérifiables.",
    unavailable: "L’analyse est momentanément indisponible. Aucune recommandation n’a été inventée.",
    resultEyebrow: "Solution vérifiable",
    knownTotal: "Total des articles",
    delivery: "Livraison à vérifier",
    confidence: "Confiance",
    style: "Style",
    why: "Pourquoi cette proposition",
    unknowns: "À vérifier",
    noSolution: "FILON s’abstient plutôt que de vous proposer un look insuffisamment documenté.",
    candidates: "offres réelles considérées",
    viewOffer: "Voir l’offre",
    inStock: "En stock observé",
    availabilityUnknown: "Disponibilité à vérifier",
    feedbackQuestion: "Cette proposition vous aide-t-elle ?",
    keep: "À garder",
    reject: "Pas pour moi",
    feedbackThanks: "Merci. Ce retour sera revu comme un signal, pas comme une préférence automatique.",
    roles: { base: "Pièce principale", footwear: "Chaussures", accessory: "Accessoire" },
    modes: {
      create: { label: "Créer", hint: "Partir d’une intention" },
      complete: { label: "Compléter", hint: "Ajouter à une pièce existante" },
      recreate: { label: "Recréer", hint: "Retrouver une direction" },
      optimize: { label: "Optimiser", hint: "Mieux utiliser un budget" },
      compare: { label: "Comparer", hint: "Arbitrer entre deux pistes" },
      discover: { label: "Inspirer", hint: "Découvrir une combinaison" },
    },
  },
  nl: {
    eyebrow: "FILON Intelligence · Fashion Expert",
    title: "Outfit Studio",
    intro: "Beschrijf je intentie. FILON stelt een oplossing samen met echte aanbiedingen en zegt duidelijk wat bekend is en wat je nog moet controleren.",
    modeLabel: "Wat wil je doen?",
    prompt: "Beschrijf je behoefte",
    placeholder: "Bijv. Een trouwjurk onder €200, met schoenen.",
    examples: ["Een trouwlook onder €200", "Een werftenue aanvullen", "Een jurk met schoenen voor een avond"],
    submit: "Een oplossing samenstellen",
    thinking: "FILON controleert echte catalogusitems…",
    disabledTitle: "Outfit Studio komt eraan",
    disabledBody: "De module staat los van de catalogus en is nog niet publiek geactiveerd. FILON maakt geen stijlaanbeveling zonder verifieerbare aanbiedingen.",
    unavailable: "De analyse is tijdelijk niet beschikbaar. Er is geen aanbeveling verzonnen.",
    resultEyebrow: "Verifieerbare oplossing",
    knownTotal: "Totaal van de artikelen",
    delivery: "Levering controleren",
    confidence: "Vertrouwen",
    style: "Stijl",
    why: "Waarom dit voorstel",
    unknowns: "Te controleren",
    noSolution: "FILON onthoudt zich liever dan een onvoldoende onderbouwde outfit voor te stellen.",
    candidates: "echte aanbiedingen bekeken",
    viewOffer: "Bekijk aanbod",
    inStock: "Voorraad waargenomen",
    availabilityUnknown: "Beschikbaarheid controleren",
    feedbackQuestion: "Helpt dit voorstel je?",
    keep: "Bewaren",
    reject: "Niet voor mij",
    feedbackThanks: "Bedankt. Deze feedback wordt als signaal bekeken, niet als automatische voorkeur.",
    roles: { base: "Hoofditem", footwear: "Schoenen", accessory: "Accessoire" },
    modes: {
      create: { label: "Maken", hint: "Vanuit een intentie" },
      complete: { label: "Aanvullen", hint: "Bij een bestaand stuk" },
      recreate: { label: "Namaken", hint: "Een richting terugvinden" },
      optimize: { label: "Optimaliseren", hint: "Een budget beter benutten" },
      compare: { label: "Vergelijken", hint: "Twee opties afwegen" },
      discover: { label: "Ontdekken", hint: "Een combinatie vinden" },
    },
  },
  en: {
    eyebrow: "FILON Intelligence · Fashion Expert",
    title: "Outfit Studio",
    intro: "Describe an intention. FILON builds a solution from real offers and clearly separates what it knows from what still needs checking.",
    modeLabel: "What would you like to do?",
    prompt: "Describe your need",
    placeholder: "E.g. A wedding dress under €200, with shoes.",
    examples: ["A wedding look under €200", "Complete a work outfit", "A dress and shoes for an evening"],
    submit: "Build a solution",
    thinking: "FILON is checking real catalogue items…",
    disabledTitle: "Outfit Studio is coming soon",
    disabledBody: "The module is isolated from the catalogue and is not publicly enabled yet. FILON does not create style recommendations without verifiable offers.",
    unavailable: "The analysis is temporarily unavailable. No recommendation has been invented.",
    resultEyebrow: "Verifiable solution",
    knownTotal: "Items total",
    delivery: "Delivery to check",
    confidence: "Confidence",
    style: "Style",
    why: "Why this proposal",
    unknowns: "To check",
    noSolution: "FILON abstains rather than suggesting an insufficiently documented outfit.",
    candidates: "real offers considered",
    viewOffer: "View offer",
    inStock: "Stock observed",
    availabilityUnknown: "Availability to check",
    feedbackQuestion: "Does this proposal help?",
    keep: "Keep it",
    reject: "Not for me",
    feedbackThanks: "Thank you. This feedback is reviewed as a signal, not stored as an automatic preference.",
    roles: { base: "Main piece", footwear: "Footwear", accessory: "Accessory" },
    modes: {
      create: { label: "Create", hint: "Start from an intention" },
      complete: { label: "Complete", hint: "Add to an owned piece" },
      recreate: { label: "Recreate", hint: "Find a direction again" },
      optimize: { label: "Optimise", hint: "Make a budget work harder" },
      compare: { label: "Compare", hint: "Arbitrate between two routes" },
      discover: { label: "Discover", hint: "Explore a combination" },
    },
  },
};

const MODES: Mode[] = ["create", "complete", "recreate", "optimize", "compare", "discover"];

function humanize(key: string, locale: Locale): string {
  const labels: Record<string, Record<Locale, string>> = {
    verified_catalog_items: { fr: "Pièces issues d’offres réelles du catalogue", nl: "Stukken uit echte catalogusaanbiedingen", en: "Pieces from real catalogue offers" },
    roles_covered: { fr: "Les rôles essentiels du look sont couverts", nl: "Essentiële rollen in de look zijn gedekt", en: "The essential outfit roles are covered" },
    within_known_budget: { fr: "Le total connu respecte le budget indiqué", nl: "Het bekende totaal blijft binnen het opgegeven budget", en: "The known total stays within the stated budget" },
    occasion_explicitly_considered: { fr: "L’occasion explicitement citée a été prise en compte", nl: "De expliciet genoemde gelegenheid is meegenomen", en: "The explicitly stated occasion was considered" },
    availability_partially_unknown: { fr: "Une disponibilité reste à confirmer", nl: "Een beschikbaarheid moet nog worden bevestigd", en: "One availability still needs confirmation" },
    delivery_unknown: { fr: "Les frais et délais de livraison ne sont pas connus", nl: "Verzendkosten en -termijnen zijn niet bekend", en: "Delivery costs and timings are not known" },
    availability_to_verify: { fr: "Une disponibilité n’est pas observée", nl: "Een beschikbaarheid is niet waargenomen", en: "One availability is not observed" },
    occasion_not_specified: { fr: "L’occasion n’a pas été précisée", nl: "De gelegenheid is niet opgegeven", en: "The occasion was not specified" },
    budget_unreachable: { fr: "Le budget connu ne permet pas une proposition vérifiable", nl: "Het bekende budget laat geen verifieerbaar voorstel toe", en: "The known budget does not allow a verifiable proposal" },
    no_verified_base: { fr: "Aucune pièce principale vérifiable n’est disponible", nl: "Er is geen verifieerbaar hoofditem beschikbaar", en: "No verifiable main piece is available" },
  };
  return labels[key]?.[locale] ?? key;
}

export function OutfitStudio() {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const [feature, setFeature] = useState<FeatureState>("loading");
  const [mode, setMode] = useState<Mode>("create");
  const [request, setRequest] = useState("");
  const [result, setResult] = useState<OutfitResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<"keep" | "reject" | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API}/api/intelligence/status`, { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) throw new Error("status_unavailable");
        return res.json();
      })
      .then((data) => setFeature(data?.modules?.outfit_studio ? "ready" : "disabled"))
      .catch((err) => {
        if (err.name !== "AbortError") setFeature("unavailable");
      });
    return () => controller.abort();
  }, []);

  const scoreLabel = useMemo(() => {
    if (!result?.solution) return null;
    return `${result.solution.confidence_score}/100`;
  }, [result]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = request.trim();
    if (trimmed.length < 2 || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setFeedback(null);
    try {
      const res = await fetch(`${API}/api/intelligence/outfit/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: trimmed, mode, locale }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        if (body?.detail?.code === "feature_disabled") setFeature("disabled");
        throw new Error("analyse_failed");
      }
      setResult((await res.json()) as OutfitResponse);
    } catch {
      setError(copy.unavailable);
    } finally {
      setBusy(false);
    }
  }

  async function sendFeedback(action: "keep" | "reject") {
    if (!result?.trace_id || feedback) return;
    setFeedback(action);
    try {
      await fetch(`${API}/api/intelligence/outfit/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trace_id: result.trace_id, action }),
      });
    } catch {
      // Le retour est volontairement non bloquant : il ne remet pas en cause la
      // solution affichée, ni ne transforme le choix en préférence implicite.
    }
  }

  return (
    <section className="os-shell" aria-labelledby="outfit-title">
      <div className="os-intro">
        <p className="os-kicker">{copy.eyebrow}</p>
        <h1 id="outfit-title">{copy.title}</h1>
        <p>{copy.intro}</p>
      </div>

      {feature === "loading" && <div className="os-panel os-status" aria-live="polite">{copy.thinking}</div>}
      {feature === "disabled" && <div className="os-panel os-status"><h2>{copy.disabledTitle}</h2><p>{copy.disabledBody}</p></div>}
      {feature === "unavailable" && <div className="os-panel os-status"><h2>{copy.unavailable}</h2></div>}

      {feature === "ready" && (
        <>
          <form className="os-panel os-form" onSubmit={submit}>
            <fieldset>
              <legend>{copy.modeLabel}</legend>
              <div className="os-modes">
                {MODES.map((value) => (
                  <button
                    type="button"
                    key={value}
                    className={mode === value ? "active" : ""}
                    onClick={() => setMode(value)}
                    aria-pressed={mode === value}
                  >
                    <strong>{copy.modes[value].label}</strong>
                    <span>{copy.modes[value].hint}</span>
                  </button>
                ))}
              </div>
            </fieldset>
            <label htmlFor="outfit-request">{copy.prompt}</label>
            <textarea
              id="outfit-request"
              value={request}
              onChange={(event) => setRequest(event.target.value)}
              placeholder={copy.placeholder}
              rows={4}
              maxLength={1000}
              required
            />
            <div className="os-examples" aria-label="Examples">
              {copy.examples.map((example) => <button type="button" key={example} onClick={() => setRequest(example)}>{example}</button>)}
            </div>
            <button className="os-submit" type="submit" disabled={busy || request.trim().length < 2}>
              {busy ? copy.thinking : copy.submit}
            </button>
          </form>

          {error && <div className="os-panel os-error" role="alert">{error}</div>}
          {result && <OutfitResult result={result} copy={copy} locale={locale} feedback={feedback} onFeedback={sendFeedback} />}
        </>
      )}
    </section>
  );
}

function OutfitResult({ result, copy, locale, feedback, onFeedback }: { result: OutfitResponse; copy: Copy; locale: Locale; feedback: "keep" | "reject" | null; onFeedback: (action: "keep" | "reject") => void }) {
  const solution = result.solution;
  if (solution.decision === "abstain") {
    return (
      <article className="os-panel os-abstain" aria-live="polite">
        <p className="os-kicker">{copy.resultEyebrow}</p>
        <h2>{copy.noSolution}</h2>
        <p>{solution.rejection_reason ? humanize(solution.rejection_reason, locale) : copy.unavailable}</p>
        <small>{result.candidates_considered} {copy.candidates}</small>
      </article>
    );
  }

  return (
    <article className="os-result" aria-live="polite">
      <header className="os-result-head">
        <div><p className="os-kicker">{copy.resultEyebrow}</p><h2>{solution.items.length} {solution.items.length > 1 ? "pieces" : "piece"}</h2></div>
        <div className="os-scores">
          <span><b>{solution.style_score}/100</b>{copy.style}</span>
          <span><b>{solution.confidence_score}/100</b>{copy.confidence}</span>
        </div>
      </header>

      <div className="os-items">
        {solution.items.map((item) => (
          <article className="os-item" key={item.offer_id}>
            <div className="os-item-image">{item.image_url ? <img src={item.image_url} alt="" /> : <span />}</div>
            <div className="os-item-body">
              <span className="os-role">{copy.roles[item.role]}</span>
              <h3>{item.name}</h3>
              {item.brand && <p>{item.brand}</p>}
              <div className="os-item-meta"><strong>{item.price?.toFixed(2)} {item.currency}</strong><span>{item.merchant.name}</span></div>
              <small>{item.availability === "in_stock" ? copy.inStock : copy.availabilityUnknown}</small>
              {item.deep_link && <a href={item.deep_link} target="_blank" rel="noreferrer">{copy.viewOffer} <span aria-hidden="true">↗</span></a>}
            </div>
          </article>
        ))}
      </div>

      <div className="os-proof-grid">
        <section><span>{copy.knownTotal}</span><strong>{solution.total_known_price?.amount.toFixed(2)} {solution.total_known_price?.currency}</strong><small>{copy.delivery}</small></section>
        <section><span>{copy.why}</span><ul>{solution.rationale_keys.map((key) => <li key={key}>{humanize(key, locale)}</li>)}</ul></section>
        <section><span>{copy.unknowns}</span><ul>{solution.unknowns.map((key) => <li key={key}>{humanize(key, locale)}</li>)}</ul></section>
      </div>

      <footer className="os-feedback">
        <p>{feedback ? copy.feedbackThanks : copy.feedbackQuestion}</p>
        {!feedback && <div><button onClick={() => onFeedback("keep")}>{copy.keep}</button><button onClick={() => onFeedback("reject")}>{copy.reject}</button></div>}
      </footer>
    </article>
  );
}
