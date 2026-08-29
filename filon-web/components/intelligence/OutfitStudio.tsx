"use client";

import { FormEvent, useEffect, useState } from "react";
import { API } from "@/lib/api";
import { normalizeSupportedCurrency } from "@/lib/currency";
import { useLocale, type Locale } from "@/lib/i18n";
import "./outfit-studio.css";

type Mode = "create" | "complete" | "recreate" | "optimize" | "compare" | "discover";
type FeatureState = "ready" | "disabled";

type OutfitItem = {
  offer_id: number;
  name: string;
  brand: string | null;
  price: number;
  currency: string;
  availability: "in_stock";
  observed_at: string;
  image_url: string | null;
  deep_link: string | null;
  role: "base" | "footwear" | "accessory";
  merchant: { name: string; region: string | null };
};

type OutfitSolution = {
  decision: "recommend" | "abstain";
  style_score: number | null;
  confidence_score: number | null;
  confidence_band: "not_calibrated";
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

const OFFER_TTL_MS = 72 * 60 * 60 * 1000;
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFreshObservation(value: unknown) {
  if (typeof value !== "string") return false;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return false;
  const age = Date.now() - timestamp;
  return age >= 0 && age <= OFFER_TTL_MS;
}

function isOutfitItem(value: unknown): value is OutfitItem {
  if (!isRecord(value) || !isRecord(value.merchant)) return false;
  return Number.isInteger(value.offer_id)
    && (value.offer_id as number) > 0
    && typeof value.name === "string"
    && value.name.trim().length > 0
    && typeof value.price === "number"
    && Number.isFinite(value.price)
    && value.price > 0
    && typeof value.currency === "string"
    && normalizeSupportedCurrency(value.currency) === value.currency
    && value.availability === "in_stock"
    && isFreshObservation(value.observed_at)
    && ["base", "footwear", "accessory"].includes(String(value.role))
    && typeof value.merchant.name === "string"
    && value.merchant.name.trim().length > 0;
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function failClosedResponse(
  traceId: string,
  candidates: number,
  reason: string,
  unknowns: string[] = [],
): OutfitResponse {
  return {
    trace_id: traceId,
    candidates_considered: candidates,
    solution: {
      decision: "abstain",
      style_score: null,
      confidence_score: null,
      confidence_band: "not_calibrated",
      total_known_price: null,
      delivery: "unknown",
      items: [],
      rationale_keys: ["abstention", reason],
      unknowns: Array.from(new Set(["confidence_not_calibrated", ...unknowns])),
      rejection_reason: reason,
    },
  };
}

function sanitizeOutfitResponse(raw: unknown, request: string): OutfitResponse | null {
  if (!isRecord(raw) || !isRecord(raw.solution)) return null;
  const traceId = typeof raw.trace_id === "string" ? raw.trace_id : "";
  const candidates = Number.isInteger(raw.candidates_considered) && (raw.candidates_considered as number) >= 0
    ? raw.candidates_considered as number
    : 0;
  const solution = raw.solution;
  if (solution.decision === "abstain") {
    return failClosedResponse(
      traceId,
      candidates,
      typeof solution.rejection_reason === "string" ? solution.rejection_reason : "invalid_evidence_contract",
      stringList(solution.unknowns),
    );
  }
  if (solution.decision !== "recommend" || !Array.isArray(solution.items) || !isRecord(solution.total_known_price)) {
    return null;
  }
  const items = solution.items;
  const total = solution.total_known_price;
  const validatedItems = items.filter(isOutfitItem);
  const validItems = items.length > 0 && validatedItems.length === items.length;
  const currencies = new Set(validatedItems.map((item) => item.currency));
  const sum = validItems
    ? validatedItems.reduce((value, item) => value + item.price, 0)
    : Number.NaN;
  const validTotal = typeof total.amount === "number"
    && Number.isFinite(total.amount)
    && total.amount > 0
    && typeof total.currency === "string"
    && currencies.size === 1
    && currencies.has(total.currency)
    && total.scope === "items_only"
    && Math.abs(sum - total.amount) <= 0.01;
  const confidenceUnknown = solution.style_score === null
    && solution.confidence_score === null
    && solution.confidence_band === "not_calibrated";
  if (!validItems || !validTotal || !confidenceUnknown) {
    return failClosedResponse(traceId, candidates, "invalid_evidence_contract", stringList(solution.unknowns));
  }
  const response: OutfitResponse = {
    trace_id: traceId,
    candidates_considered: candidates,
    solution: {
      decision: "recommend",
      style_score: null,
      confidence_score: null,
      confidence_band: "not_calibrated",
      total_known_price: { amount: total.amount as number, currency: total.currency as string, scope: "items_only" },
      delivery: "unknown",
      items: validatedItems,
      rationale_keys: stringList(solution.rationale_keys),
      unknowns: stringList(solution.unknowns),
      rejection_reason: null,
    },
  };
  return abstainForIncompatibleSolution(response, request);
}

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
  itemSingular: string;
  itemPlural: string;
  knownTotal: string;
  delivery: string;
  confidence: string;
  style: string;
  notMeasured: string;
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
    eyebrow: "FILON Intelligence · Décision fondée sur des preuves",
    title: "Outfit Studio",
    intro: "Décrivez une tenue, un kit ou un besoin. FILON sélectionne des offres réelles, puis distingue clairement ce qu’il sait de ce qui reste à vérifier.",
    modeLabel: "Que voulez-vous faire ?",
    prompt: "Décrivez votre besoin ou votre kit",
    placeholder: "Ex. Des vêtements de tennis sous 200 €, ou un kit camping.",
    examples: ["Des vêtements de tennis sous 200 €", "Un kit camping sous 300 €", "Une robe avec chaussures pour une soirée"],
    submit: "Construire une solution",
    thinking: "FILON vérifie les pièces réelles du catalogue…",
    disabledTitle: "Outfit Studio arrive bientôt",
    disabledBody: "Le module est isolé du catalogue et n’est pas encore activé publiquement. FILON ne crée pas de recommandation de style sans offres vérifiables.",
    unavailable: "L’analyse est momentanément indisponible. Aucune recommandation n’a été inventée.",
    resultEyebrow: "Sélection vérifiable",
    itemSingular: "article",
    itemPlural: "articles",
    knownTotal: "Total des articles",
    delivery: "Livraison à vérifier",
    confidence: "Confiance des preuves",
    style: "Couverture documentée",
    notMeasured: "Non mesuré",
    why: "Pourquoi cette proposition",
    unknowns: "À vérifier",
    noSolution: "FILON s’abstient plutôt que de proposer une sélection insuffisamment documentée.",
    candidates: "offres réelles considérées",
    viewOffer: "Voir l’offre",
    inStock: "En stock observé",
    availabilityUnknown: "Disponibilité à vérifier",
    feedbackQuestion: "Cette proposition vous aide-t-elle ?",
    keep: "À garder",
    reject: "Pas pour moi",
    feedbackThanks: "Merci. Ce retour sera revu comme un signal, pas comme une préférence automatique.",
    roles: { base: "Article sélectionné", footwear: "Chaussures", accessory: "Accessoire" },
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
    eyebrow: "FILON Intelligence · Beslissen op bewijs",
    title: "Outfit Studio",
    intro: "Beschrijf een outfit, kit of behoefte. FILON selecteert echte aanbiedingen en maakt duidelijk wat bekend is en wat je nog moet controleren.",
    modeLabel: "Wat wil je doen?",
    prompt: "Beschrijf je behoefte of kit",
    placeholder: "Bijv. Tenniskleding onder €200, of een kampeerkit.",
    examples: ["Tenniskleding onder €200", "Kampeeruitrusting onder €300", "Een jurk met schoenen voor een avond"],
    submit: "Een oplossing samenstellen",
    thinking: "FILON controleert echte catalogusitems…",
    disabledTitle: "Outfit Studio komt eraan",
    disabledBody: "De module staat los van de catalogus en is nog niet publiek geactiveerd. FILON maakt geen stijlaanbeveling zonder verifieerbare aanbiedingen.",
    unavailable: "De analyse is tijdelijk niet beschikbaar. Er is geen aanbeveling verzonnen.",
    resultEyebrow: "Verifieerbare selectie",
    itemSingular: "artikel",
    itemPlural: "artikelen",
    knownTotal: "Totaal van de artikelen",
    delivery: "Levering controleren",
    confidence: "Bewijsvertrouwen",
    style: "Gedocumenteerde dekking",
    notMeasured: "Niet gemeten",
    why: "Waarom dit voorstel",
    unknowns: "Te controleren",
    noSolution: "FILON onthoudt zich liever dan een onvoldoende onderbouwde selectie voor te stellen.",
    candidates: "echte aanbiedingen bekeken",
    viewOffer: "Bekijk aanbod",
    inStock: "Voorraad waargenomen",
    availabilityUnknown: "Beschikbaarheid controleren",
    feedbackQuestion: "Helpt dit voorstel je?",
    keep: "Bewaren",
    reject: "Niet voor mij",
    feedbackThanks: "Bedankt. Deze feedback wordt als signaal bekeken, niet als automatische voorkeur.",
    roles: { base: "Geselecteerd artikel", footwear: "Schoenen", accessory: "Accessoire" },
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
    eyebrow: "FILON Intelligence · Evidence-led decisions",
    title: "Outfit Studio",
    intro: "Describe an outfit, a kit or a need. FILON selects real offers and clearly separates what it knows from what still needs checking.",
    modeLabel: "What would you like to do?",
    prompt: "Describe your need or kit",
    placeholder: "E.g. Tennis clothing under €200, or a camping kit.",
    examples: ["Tennis clothing under €200", "Camping equipment under €300", "A dress and shoes for an evening"],
    submit: "Build a solution",
    thinking: "FILON is checking real catalogue items…",
    disabledTitle: "Outfit Studio is coming soon",
    disabledBody: "The module is isolated from the catalogue and is not publicly enabled yet. FILON does not create style recommendations without verifiable offers.",
    unavailable: "The analysis is temporarily unavailable. No recommendation has been invented.",
    resultEyebrow: "Verifiable selection",
    itemSingular: "item",
    itemPlural: "items",
    knownTotal: "Items total",
    delivery: "Delivery to check",
    confidence: "Evidence confidence",
    style: "Documented coverage",
    notMeasured: "Not measured",
    why: "Why this proposal",
    unknowns: "To check",
    noSolution: "FILON abstains rather than suggesting an insufficiently documented selection.",
    candidates: "real offers considered",
    viewOffer: "View offer",
    inStock: "Stock observed",
    availabilityUnknown: "Availability to check",
    feedbackQuestion: "Does this proposal help?",
    keep: "Keep it",
    reject: "Not for me",
    feedbackThanks: "Thank you. This feedback is reviewed as a signal, not stored as an automatic preference.",
    roles: { base: "Selected item", footwear: "Footwear", accessory: "Accessory" },
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
const ANALYSIS_TIMEOUT_MS = 25_000;

// Dernier filet de décision côté interface : il ne reclasse rien et n’invente
// jamais une pièce. Il bloque seulement les rôles « base » dont le propre titre
// prouve qu’il s’agit d’un accessoire, d’un sous-vêtement ou d’une gaine.
const INVALID_BASE_ITEM = /\b(?:jewell?ery|necklace|earrings?|bracelets?|rings?|colliers?|boucles?|bagues?|bra|underwear|lingerie|bralette|soutien[- ]?gorge|body\s*shaper|shapewear|tummy\s*control|waist\s*trainer|bridal\s+veil|veil|voile|accessories?)\b/i;
const INVALID_FOOTWEAR_ITEM = /\b(?:panel|regulateur|régulateur|verstellfuss|height\s*adjust|wood|bois)\b/i;
const INVALID_ACCESSORY_ITEM = /\b(?:toiletry\s*bag|washable\s+kraft|trousse\s+de\s+toilette)\b/i;

// Quand l’utilisateur demande une pièce précise, elle doit être prouvée par
// le titre d’au moins une offre. Un mot technique isolé (ex. « SHOES » sur un
// régulateur de panneau) ne suffit pas à constituer des chaussures.
const REQUESTED_ITEM_EVIDENCE: ReadonlyArray<{ request: RegExp; item: RegExp; invalid?: RegExp }> = [
  { request: /\b(?:veil|voile)\b/i, item: /\b(?:veil|voile)\b/i },
  { request: /\b(?:shoe|shoes|chaussure|chaussures|schoenen|footwear)\b/i, item: /\b(?:shoe|shoes|chaussure|chaussures|schoenen|boots?|bottines?|sandals?|sandales?|sneakers?|baskets?|heels?|talons?)\b/i, invalid: INVALID_FOOTWEAR_ITEM },
];

function hasInvalidMainPiece(solution: OutfitSolution) {
  const mainPiece = solution.items.find((item) => item.role === "base");
  return Boolean(mainPiece && INVALID_BASE_ITEM.test(mainPiece.name));
}

function hasInvalidSupportingPiece(solution: OutfitSolution) {
  return solution.items.some((item) =>
    (item.role === "footwear" && INVALID_FOOTWEAR_ITEM.test(item.name))
    || (item.role === "accessory" && INVALID_ACCESSORY_ITEM.test(item.name)),
  );
}

function lacksRequestedItemEvidence(request: string, solution: OutfitSolution) {
  return REQUESTED_ITEM_EVIDENCE.some(({ request: requested, item, invalid }) =>
    requested.test(request) && !solution.items.some((offer) => item.test(offer.name) && !(invalid?.test(offer.name))),
  );
}

function abstainForIncompatibleSolution(response: OutfitResponse, request: string): OutfitResponse {
  const rejectionReason = hasInvalidMainPiece(response.solution)
    ? "no_verified_base"
    : hasInvalidSupportingPiece(response.solution)
      ? "no_verified_outfit_item"
    : lacksRequestedItemEvidence(request, response.solution)
      ? "no_verified_requested_item"
      : null;
  if (!rejectionReason) return response;
  return {
    ...response,
    solution: {
      ...response.solution,
      decision: "abstain",
      total_known_price: null,
      items: [],
      rejection_reason: rejectionReason,
    },
  };
}

function humanize(key: string, locale: Locale): string {
  const labels: Record<string, Record<Locale, string>> = {
    verified_catalog_items: { fr: "Pièces issues d’offres réelles du catalogue", nl: "Stukken uit echte catalogusaanbiedingen", en: "Pieces from real catalogue offers" },
    roles_covered: { fr: "Les rôles essentiels du look sont couverts", nl: "Essentiële rollen in de look zijn gedekt", en: "The essential outfit roles are covered" },
    within_known_budget: { fr: "Le total connu respecte le budget indiqué", nl: "Het bekende totaal blijft binnen het opgegeven budget", en: "The known total stays within the stated budget" },
    occasion_recorded_not_verified: { fr: "L’occasion citée est enregistrée, mais sa compatibilité n’est pas vérifiée", nl: "De genoemde gelegenheid is geregistreerd, maar de compatibiliteit is niet geverifieerd", en: "The stated occasion is recorded, but compatibility is not verified" },
    availability_partially_unknown: { fr: "Une disponibilité reste à confirmer", nl: "Een beschikbaarheid moet nog worden bevestigd", en: "One availability still needs confirmation" },
    delivery_unknown: { fr: "Les frais et délais de livraison ne sont pas connus", nl: "Verzendkosten en -termijnen zijn niet bekend", en: "Delivery costs and timings are not known" },
    availability_to_verify: { fr: "Une disponibilité n’est pas observée", nl: "Een beschikbaarheid is niet waargenomen", en: "One availability is not observed" },
    occasion_not_specified: { fr: "L’occasion n’a pas été précisée", nl: "De gelegenheid is niet opgegeven", en: "The occasion was not specified" },
    occasion_not_verified: { fr: "La compatibilité avec l’occasion n’est pas vérifiée", nl: "De compatibiliteit met de gelegenheid is niet geverifieerd", en: "Compatibility with the occasion is not verified" },
    style_compatibility_not_verified: { fr: "La compatibilité de style et de coupe n’est pas vérifiée", nl: "De stijl- en pasvormcompatibiliteit is niet geverifieerd", en: "Style and fit compatibility are not verified" },
    confidence_not_calibrated: { fr: "La confiance n’est pas encore mesurée sur un jeu indépendant", nl: "Het vertrouwen is nog niet gemeten op een onafhankelijke dataset", en: "Confidence has not yet been measured on an independent dataset" },
    budget_unreachable: { fr: "Le budget connu ne permet pas une proposition vérifiable", nl: "Het bekende budget laat geen verifieerbaar voorstel toe", en: "The known budget does not allow a verifiable proposal" },
    no_verified_base: { fr: "Aucune pièce principale vérifiable n’est disponible", nl: "Er is geen verifieerbaar hoofditem beschikbaar", en: "No verifiable main piece is available" },
    no_verified_requested_item: { fr: "Aucune offre ne prouve la pièce explicitement demandée", nl: "Geen aanbieding bewijst het expliciet gevraagde item", en: "No offer proves that the explicitly requested item is available" },
    no_verified_outfit_item: { fr: "Une pièce de la tenue n’est pas un article vestimentaire vérifiable", nl: "Een onderdeel van de outfit is geen verifieerbaar kledingartikel", en: "An item in the outfit is not a verifiable fashion item" },
    invalid_evidence_contract: { fr: "Les preuves reçues sont incomplètes ou incohérentes", nl: "Het ontvangen bewijs is onvolledig of tegenstrijdig", en: "The received evidence is incomplete or inconsistent" },
    taxonomy_resolved: { fr: "La catégorie de chaque article a été identifiée", nl: "De categorie van elk artikel is vastgesteld", en: "Each item category was identified" },
    constraints_checked: { fr: "Les contraintes explicites ont été contrôlées", nl: "De expliciete beperkingen zijn gecontroleerd", en: "The explicit constraints were checked" },
    cross_item_compatibility_not_verified: { fr: "La compatibilité entre les articles n’est pas vérifiée", nl: "De onderlinge compatibiliteit van de artikelen is niet geverifieerd", en: "Compatibility between items is not verified" },
    intent_not_resolved: { fr: "Le besoin demandé n’a pas pu être identifié avec certitude", nl: "De gevraagde behoefte kon niet met zekerheid worden vastgesteld", en: "The requested need could not be resolved with certainty" },
    no_verified_scope: { fr: "Aucun périmètre d’offres vérifiables n’a été trouvé", nl: "Er is geen bereik met verifieerbare aanbiedingen gevonden", en: "No scope of verifiable offers was found" },
    no_eligible_offer: { fr: "Aucune offre ne satisfait les preuves requises", nl: "Geen aanbod voldoet aan de vereiste bewijzen", en: "No offer meets the required evidence" },
    currency_not_comparable: { fr: "Les prix ne partagent pas une devise comparable", nl: "De prijzen delen geen vergelijkbare valuta", en: "The prices do not share a comparable currency" },
    non_finite_total: { fr: "Le total des prix n’est pas calculable de façon fiable", nl: "Het prijstotaal kan niet betrouwbaar worden berekend", en: "The price total cannot be calculated reliably" },
  };
  return labels[key]?.[locale] ?? key;
}

export function OutfitStudio() {
  const { locale } = useLocale();
  const copy = COPY[locale];
  // Le formulaire ne doit pas attendre un contrôle de statut réseau : la
  // validation définitive reste celle de l’endpoint d’analyse. Cela élimine
  // le squelette bloquant sans masquer un désactivation explicite du module.
  const [feature, setFeature] = useState<FeatureState>("ready");
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
      .catch(() => {
        // Un contrôle de statut indisponible ne rend pas l’outil indisponible :
        // on laisse l’utilisateur soumettre, puis l’endpoint d’analyse fournit
        // une réponse explicite ou un état d’erreur honnête.
      });
    return () => controller.abort();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = request.trim();
    if (trimmed.length < 2 || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setFeedback(null);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), ANALYSIS_TIMEOUT_MS);
    try {
      const res = await fetch(`${API}/api/intelligence/outfit/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: trimmed, mode, locale }),
        signal: controller.signal,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        if (body?.detail?.code === "feature_disabled") setFeature("disabled");
        throw new Error("analyse_failed");
      }
      const response = sanitizeOutfitResponse(await res.json(), trimmed);
      if (!response) throw new Error("invalid_evidence_contract");
      setResult(response);
    } catch {
      setError(copy.unavailable);
    } finally {
      window.clearTimeout(timeout);
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

      {feature === "disabled" && <div className="os-panel os-status"><h2>{copy.disabledTitle}</h2><p>{copy.disabledBody}</p></div>}

      {feature === "ready" && (
        <>
          <form className="os-panel os-form" onSubmit={submit} aria-busy={busy}>
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
              {copy.submit}
            </button>
            {busy && <p className="os-analysis-status" aria-live="polite">{copy.thinking}</p>}
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
        <div><p className="os-kicker">{copy.resultEyebrow}</p><h2>{solution.items.length} {solution.items.length > 1 ? copy.itemPlural : copy.itemSingular}</h2></div>
        <div className="os-scores">
          <span><b>{copy.notMeasured}</b>{copy.style}</span>
          <span><b>{copy.notMeasured}</b>{copy.confidence}</span>
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
              <div className="os-item-meta"><strong>{item.price.toFixed(2)} {item.currency}</strong><span>{item.merchant.name}</span></div>
              <small>{copy.inStock}</small>
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
