import {
  FILON_API_BASE_URL,
  getFirstImageUrl,
  isFilonObservationFresh,
  normalizeFilonCurrency,
  normalizeFilonObservedAt,
  type FilonCurrency,
} from "./filon-api";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type FilonAdviceCard = {
  offerId: number;
  productEan: string | null;
  rank: string;
  name: string;
  price: number;
  currency: FilonCurrency;
  merchant: string;
  inStock: true;
  observedAt: string;
  evidenceCurrent: true;
  imageUrl: string | null;
  link: string | null;
  why: string;
  buy: boolean;
};

export type FilonAdvice = {
  usage: string;
  offers: number;
  real: boolean;
  cards: FilonAdviceCard[];
};

type RawAdviceCard = Partial<Omit<FilonAdviceCard, "offerId" | "productEan" | "imageUrl" | "inStock" | "observedAt" | "evidenceCurrent">> & { image?: string | null; offer_id?: number | null; product_ean?: string | null; in_stock?: boolean | null; observed_at?: string | null; evidence_current?: boolean | null };
type AdviceEvent = {
  type?: string;
  data?: Omit<Partial<FilonAdvice>, "cards"> & { cards?: RawAdviceCard[] };
  message?: string;
};

function normalizeAdvice(raw: AdviceEvent["data"], now: number | Date): FilonAdvice {
  if (raw?.real !== true) return { usage: typeof raw?.usage === "string" ? raw.usage : "votre besoin", offers: 0, real: false, cards: [] };
  const cards = (raw?.cards ?? []).reduce<FilonAdviceCard[]>((valid, card) => {
    const currency = normalizeFilonCurrency(card.currency);
    const observedAt = normalizeFilonObservedAt(card.observed_at);
    const link = typeof card.link === "string" && isSafePartnerOfferUrl(card.link.trim())
      ? card.link.trim()
      : null;
    if (
      typeof card?.offer_id !== "number"
      || !Number.isInteger(card.offer_id)
      || card.offer_id <= 0
      || typeof card.name !== "string"
      || !card.name.trim()
      || typeof card.price !== "number"
      || !Number.isFinite(card.price)
      || card.price <= 0
      || currency === null
      || typeof card.merchant !== "string"
      || !card.merchant.trim()
      || card.in_stock !== true
      || observedAt === null
      || !isFilonObservationFresh(observedAt, now)
      || card.evidence_current !== true
    ) {
      return valid;
    }
    valid.push({
      offerId: card.offer_id,
      productEan: typeof card.product_ean === "string" && card.product_ean.trim() ? card.product_ean.trim() : null,
      // Ces champs narratifs amont ne sont pas une preuve. Des jetons neutres
      // empêchent un rang, une raison ou un signal d'achat généré de devenir
      // une affirmation publique non rapprochée.
      rank: "catalogue_current",
      name: card.name.trim(),
      price: card.price,
      currency,
      merchant: card.merchant.trim(),
      inStock: true,
      observedAt,
      // Les cartes Assistant proviennent de la passerelle de preuve qui lie
      // explicitement ce prix, cette devise et ce stock au même snapshot.
      evidenceCurrent: true,
      imageUrl: getFirstImageUrl(typeof card.image === "string" ? card.image : null),
      link,
      why: "current_offer_evidence",
      buy: false,
    });
    return valid;
  }, []);
  return {
    usage: typeof raw?.usage === "string" ? raw.usage : "votre besoin",
    // Le mobile ne revendique que les cartes dont il a lui-même validé les
    // preuves minimales, pas un total amont impossible à auditer ici.
    offers: cards.length,
    real: cards.length > 0,
    cards,
  };
}

export function parseFilonAdviceSse(payload: string, now: number | Date = Date.now()): FilonAdvice {
  const events = payload.split(/\n\n+/);
  for (const event of events.reverse()) {
    const line = event.split("\n").find((item) => item.startsWith("data: "));
    if (!line) continue;
    const parsed = JSON.parse(line.slice(6)) as AdviceEvent;
    if (parsed.type === "error") throw new Error(parsed.message || "Assistant indisponible");
    if (parsed.type === "results") return normalizeAdvice(parsed.data, now);
  }
  throw new Error("Réponse Assistant incomplète");
}

export async function askFilonAssistant(query: string, locale: "fr" | "nl" | "en"): Promise<FilonAdvice> {
  const params = new URLSearchParams({ q: query.trim(), locale, country: "be" });
  const response = await fetch(`${FILON_API_BASE_URL}/api/advise/stream?${params.toString()}`, {
    headers: { Accept: "text/event-stream" },
  });
  if (!response.ok) throw new Error(`Assistant indisponible (${response.status})`);
  return parseFilonAdviceSse(await response.text());
}
