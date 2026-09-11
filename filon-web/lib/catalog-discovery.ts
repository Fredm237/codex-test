export type CatalogDiscoveryItem = {
  id: number;
  name: string;
  brand?: string | null;
  category?: string | null;
  subcategory?: string | null;
  image?: string | null;
  merchant: { name: string };
};

const SMARTPHONE_QUERY = /\b(?:iphone|galaxy|smartphone|t[ée]l[ée]phones?|gsm)\b/i;
const SMARTPHONE_IMPOSTOR = /\b(?:cam[ée]ra|lunettes?|coque|cover|case|housse|verre|glass|chargeur|charger|c[âa]ble|adaptateur|support|bracelet|band|strap|pi[èe]ce|repair|[ée]cran|screen|batterie)\b/i;
const LAPTOP_QUERY = /\b(?:macbook|laptop|notebook|ordinateur portable|pc portable)\b/i;
const LAPTOP_IMPOSTOR = /\b(?:extenseur|second [ée]cran|[ée]cran (?:externe|portable)|ram|m[ée]moire|carte m[èe]re|motherboard|batterie|chargeur|adaptateur|housse|sacoche|support|clavier|pi[èe]ce|replacement|remplacement)\b/i;
const HEADPHONE_QUERY = /\b(?:casque|headphones?|headsets?|[ée]couteurs?|earbuds?|koptelefoon)\b/i;
const HEADPHONE_IMPOSTOR = /\b(?:casquettes?|moto|interphone|protection auditive|prot[èe]ge-oreilles|tir|t-shirt|adaptateur|impedance|helmet)\b/i;
const FASHION_IMPOSTOR = /\b(?:patron|tissu|dentelle|ruban|yard|couture|garniture|breloque|bouton|fermeture|patch|[ée]cusson|cintre|rangement|meuble|languette|serrage|couvre-chaussure|lacets?|accessoires?|d[ée]coration|bricolage)\b/i;
const FASHION_TERM = /^(?:robe|veste|chemise|pantalon|chaussure)$/i;

const INTENTS: ReadonlyArray<[RegExp, string]> = [
  [/\b(?:iphone|galaxy|smartphone|t[ée]l[ée]phones?|gsm)\b/i, "smartphone"],
  [/\b(?:macbook|laptop|notebook|ordinateur|pc portable)\b/i, "ordinateur portable"],
  [/\b(?:casque|headphone|koptelefoon|[ée]couteurs?|earbuds?)\b/i, "casque audio"],
  [/\b(?:robes?|dresses?|jurken?)\b/i, "robe"],
  [/\b(?:vestes?|jackets?|jassen?)\b/i, "veste"],
  [/\b(?:pantalons?|trousers?|broeken?)\b/i, "pantalon"],
  [/\b(?:chaussures?|shoes?|schoenen?|sneakers?)\b/i, "chaussure"],
];

const OUTFIT_TERMS: ReadonlyArray<[RegExp, string]> = [
  [/\b(?:robes?|dresses?|jurken?)\b/i, "robe"],
  [/\b(?:vestes?|jackets?|jassen?)\b/i, "veste"],
  [/\b(?:chemises?|shirts?|overhemden?)\b/i, "chemise"],
  [/\b(?:pantalons?|trousers?|broeken?)\b/i, "pantalon"],
  [/\b(?:chaussures?|shoes?|schoenen?|sneakers?)\b/i, "chaussure"],
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isItem(value: unknown): value is CatalogDiscoveryItem {
  if (!isRecord(value) || !isRecord(value.merchant)) return false;
  return Number.isInteger(value.id)
    && (value.id as number) > 0
    && typeof value.name === "string"
    && value.name.trim().length > 0
    && typeof value.merchant.name === "string";
}

function relevantTo(query: string, item: CatalogDiscoveryItem) {
  if (SMARTPHONE_QUERY.test(query)) {
    if (SMARTPHONE_IMPOSTOR.test(item.name)) return false;
    if (item.subcategory !== "Smartphones") return false;
    const exactModel = query.match(/\b(?:iphone|galaxy)\s+[a-z0-9-]+/i)?.[0];
    return exactModel ? item.name.toLocaleLowerCase().includes(exactModel.toLocaleLowerCase()) : true;
  }
  if (LAPTOP_QUERY.test(query)) {
    if (LAPTOP_IMPOSTOR.test(item.name)) return false;
    return item.subcategory === "Ordinateurs portables"
      && LAPTOP_QUERY.test(item.name);
  }
  if (HEADPHONE_QUERY.test(query)) {
    if (HEADPHONE_IMPOSTOR.test(item.name)) return false;
    const section = `${item.category || ""} ${item.subcategory || ""}`;
    return HEADPHONE_QUERY.test(item.name)
      && /(?:Casques audio|Écouteurs|Gaming|TV & Son|Téléphonie)/i.test(section);
  }
  if (FASHION_TERM.test(query)) {
    if (FASHION_IMPOSTOR.test(item.name)) return false;
    return /^(?:Mode(?: femme| homme| enfant)?|Chaussures)$/i.test(item.category || "");
  }
  return true;
}

async function lookup(query: string, signal: AbortSignal): Promise<CatalogDiscoveryItem[]> {
  // Même origine en production : Vercel relaie ce chemin vers Railway. Cela
  // garde le catalogue accessible depuis le domaine public et les previews,
  // sans dépendre de la liste CORS propre à chaque URL de déploiement.
  const upstream = new URL("/api/catalog/offers/", window.location.origin);
  upstream.searchParams.set("q", query);
  upstream.searchParams.set("limit", "50");
  if (FASHION_TERM.test(query)) upstream.searchParams.set("price_min", "20");

  const response = await fetch(upstream, {
    cache: "no-store",
    headers: { accept: "application/json" },
    signal,
  });
  if (!response.ok) return [];
  const body: unknown = await response.json();
  if (!isRecord(body) || !Array.isArray(body.items)) return [];

  const unique = new Map<string, CatalogDiscoveryItem>();
  for (const item of body.items.filter(isItem)) {
    if (!relevantTo(query, item)) continue;
    const key = item.name.trim().toLocaleLowerCase();
    if (!unique.has(key)) unique.set(key, item);
  }
  return Array.from(unique.values()).slice(0, 8);
}

export async function discoverCatalogue(
  rawQuery: string,
  signal: AbortSignal,
  surface: "search" | "outfit" = "search",
): Promise<CatalogDiscoveryItem[]> {
  const query = rawQuery.trim().slice(0, 180);
  if (query.length < 2) return [];

  if (surface === "outfit") {
    const requested = OUTFIT_TERMS.filter(([pattern]) => pattern.test(query)).map(([, term]) => term);
    const terms = requested.length ? requested : ["veste", "pantalon", "chaussure"];
    const groups = await Promise.all(terms.slice(0, 3).map((term) => lookup(term, signal)));
    const unique = new Map<number, CatalogDiscoveryItem>();
    for (const group of groups) {
      for (const item of group.slice(0, 3)) unique.set(item.id, item);
    }
    return Array.from(unique.values()).slice(0, 8);
  }

  let items = await lookup(query, signal);
  if (!items.length) {
    const fallback = INTENTS.find(([pattern]) => pattern.test(query))?.[1];
    if (fallback && fallback.toLocaleLowerCase() !== query.toLocaleLowerCase()) {
      items = await lookup(fallback, signal);
    }
  }
  return items;
}
