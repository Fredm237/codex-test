import { FILON_API_BASE_URL, getFirstImageUrl } from "./filon-api";

export type FilonAdviceCard = {
  offerId: number | null;
  productEan: string | null;
  rank: string;
  name: string;
  price: number;
  merchant: string;
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

type RawAdviceCard = Partial<Omit<FilonAdviceCard, "offerId" | "productEan">> & { image?: string | null; offer_id?: number | null; product_ean?: string | null };
type AdviceEvent = {
  type?: string;
  data?: Omit<Partial<FilonAdvice>, "cards"> & { cards?: RawAdviceCard[] };
  message?: string;
};

function normalizeAdvice(raw: AdviceEvent["data"]): FilonAdvice {
  const cards = (raw?.cards ?? []).reduce<FilonAdviceCard[]>((valid, card) => {
    if (typeof card?.name !== "string" || typeof card.price !== "number" || typeof card.merchant !== "string") {
      return valid;
    }
    valid.push({
      offerId: typeof card.offer_id === "number" ? card.offer_id : null,
      productEan: typeof card.product_ean === "string" && card.product_ean.trim() ? card.product_ean.trim() : null,
      rank: typeof card.rank === "string" ? card.rank : "Sélection FILON",
      name: card.name,
      price: card.price,
      merchant: card.merchant,
      imageUrl: getFirstImageUrl(typeof card.image === "string" ? card.image : null),
      link: typeof card.link === "string" && /^https:\/\//.test(card.link) ? card.link : null,
      why: typeof card.why === "string" ? card.why : "Offre vérifiée du catalogue FILON.",
      buy: card.buy !== false,
    });
    return valid;
  }, []);
  return {
    usage: typeof raw?.usage === "string" ? raw.usage : "votre besoin",
    offers: typeof raw?.offers === "number" ? raw.offers : 0,
    real: raw?.real === true,
    cards,
  };
}

export function parseFilonAdviceSse(payload: string): FilonAdvice {
  const events = payload.split(/\n\n+/);
  for (const event of events.reverse()) {
    const line = event.split("\n").find((item) => item.startsWith("data: "));
    if (!line) continue;
    const parsed = JSON.parse(line.slice(6)) as AdviceEvent;
    if (parsed.type === "error") throw new Error(parsed.message || "Assistant indisponible");
    if (parsed.type === "results") return normalizeAdvice(parsed.data);
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
