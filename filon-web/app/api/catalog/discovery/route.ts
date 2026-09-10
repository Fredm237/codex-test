import { NextRequest, NextResponse } from "next/server";

import { API } from "@/lib/api";

export const dynamic = "force-dynamic";

const MAX_QUERY_LENGTH = 180;
const MAX_ITEMS = 12;

type DiscoveryItem = {
  id: number;
  name: string;
  brand: string | null;
  category: string | null;
  subcategory?: string | null;
  image: string | null;
  merchant: { name: string };
  price: number | null;
  currency: string | null;
  evidence_current: boolean;
};

const SMARTPHONE_QUERY = /\b(?:iphone|galaxy|smartphone|t[ée]l[ée]phone|gsm)\b/i;
const SMARTPHONE_IMPOSTOR = /\b(?:cam[ée]ra|lunettes?|coque|cover|case|housse|verre|glass|chargeur|charger|c[âa]ble|adaptateur|support|bracelet|band|strap|pi[èe]ce|repair|[ée]cran|screen|batterie)\b/i;
const FASHION_IMPOSTOR = /\b(?:patron|tissu|dentelle|ruban|yard|couture|garniture|breloque|bouton|fermeture|patch|[ée]cusson|cintre|rangement|meuble|languette|serrage|couvre-chaussure|lacets?|accessoires?|d[ée]coration|bricolage)\b/i;

function relevantTo(query: string, item: DiscoveryItem) {
  if (SMARTPHONE_QUERY.test(query)) {
    if (SMARTPHONE_IMPOSTOR.test(item.name)) return false;
    if (item.subcategory !== "Smartphones") return false;
    const exactModel = query.match(/\b(?:iphone|galaxy)\s+[a-z0-9-]+/i)?.[0];
    return exactModel ? item.name.toLocaleLowerCase().includes(exactModel.toLocaleLowerCase()) : true;
  }
  if (/^(?:robe|veste|chemise|pantalon|chaussure)$/i.test(query)) {
    if (FASHION_IMPOSTOR.test(item.name)) return false;
    const category = item.category || "";
    return /^(?:Mode(?: femme| homme| enfant)?|Chaussures)$/i.test(category);
  }
  return true;
}

const INTENTS: ReadonlyArray<[RegExp, string]> = [
  [/\b(?:iphone|galaxy|smartphone|t[ée]l[ée]phone|gsm)\b/i, "smartphone"],
  [/\b(?:macbook|laptop|notebook|ordinateur|pc portable)\b/i, "ordinateur portable"],
  [/\b(?:casque|headphone|koptelefoon|[ée]couteur|earbud)\b/i, "casque"],
  [/\b(?:robe|dress|jurk)\b/i, "robe"],
  [/\b(?:veste|jacket|jas)\b/i, "veste"],
  [/\b(?:pantalon|trouser|broek)\b/i, "pantalon"],
  [/\b(?:chaussure|shoe|schoen|sneaker)\b/i, "chaussure"],
  [/\b(?:tenue|outfit|look|mariage|soir[ée]e)\b/i, "veste"],
];

function isItem(value: unknown): value is DiscoveryItem {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  const merchant = item.merchant as Record<string, unknown> | null;
  return Number.isInteger(item.id)
    && (item.id as number) > 0
    && typeof item.name === "string"
    && item.name.trim().length > 0
    && Boolean(merchant && typeof merchant.name === "string");
}

async function lookup(query: string): Promise<DiscoveryItem[]> {
  const upstream = new URL("/api/catalog/offers", API);
  upstream.searchParams.set("q", query);
  // Une marge est nécessaire avant le filtre de pertinence : certains feeds
  // classent d'abord des accessoires compatibles avec le produit demandé.
  upstream.searchParams.set("limit", "50");
  if (/^(?:robe|veste|chemise|pantalon|chaussure)$/i.test(query)) {
    upstream.searchParams.set("price_min", "20");
  }
  const response = await fetch(upstream, {
    cache: "no-store",
    headers: { accept: "application/json" },
    signal: AbortSignal.timeout(12_000),
  });
  if (!response.ok) return [];
  const body: unknown = await response.json();
  if (!body || typeof body !== "object" || Array.isArray(body)) return [];
  const items = (body as { items?: unknown }).items;
  if (!Array.isArray(items)) return [];
  const unique = new Map<string, DiscoveryItem>();
  for (const item of items.filter(isItem)) {
    if (!relevantTo(query, item)) continue;
    const key = item.name.trim().toLocaleLowerCase();
    if (!unique.has(key)) unique.set(key, item);
  }
  return Array.from(unique.values()).slice(0, 8);
}

export async function GET(request: NextRequest) {
  const raw = (request.nextUrl.searchParams.get("q") || "").trim();
  if (raw.length < 2 || raw.length > MAX_QUERY_LENGTH) {
    return NextResponse.json({ items: [] }, { status: 400 });
  }

  try {
    if (request.nextUrl.searchParams.get("surface") === "outfit") {
      const requested: string[] = [];
      const outfitTerms: ReadonlyArray<[RegExp, string]> = [
        [/\b(?:robes?|dresses?|jurken?)\b/i, "robe"],
        [/\b(?:vestes?|jackets?|jassen?)\b/i, "veste"],
        [/\b(?:chemises?|shirts?|overhemden?)\b/i, "chemise"],
        [/\b(?:pantalons?|trousers?|broeken?)\b/i, "pantalon"],
        [/\b(?:chaussures?|shoes?|schoenen?|sneakers?)\b/i, "chaussure"],
      ];
      for (const [pattern, query] of outfitTerms) {
        if (pattern.test(raw)) requested.push(query);
      }
      if (!requested.length) requested.push("veste", "pantalon", "chaussure");
      const groups = await Promise.all(requested.slice(0, 3).map(lookup));
      const unique = new Map<number, DiscoveryItem>();
      for (const group of groups) {
        for (const item of group.slice(0, 3)) unique.set(item.id, item);
      }
      return NextResponse.json(
        { items: Array.from(unique.values()).slice(0, 8) },
        { headers: { "Cache-Control": "no-store" } },
      );
    }
    let items = await lookup(raw);
    if (!items.length) {
      const fallback = INTENTS.find(([pattern]) => pattern.test(raw))?.[1];
      if (fallback && fallback.toLocaleLowerCase() !== raw.toLocaleLowerCase()) {
        items = await lookup(fallback);
      }
    }
    return NextResponse.json(
      { items },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return NextResponse.json(
      { items: [] },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
