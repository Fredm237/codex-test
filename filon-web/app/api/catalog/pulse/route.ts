import { NextResponse } from "next/server";
import { API } from "@/lib/api";

// Les navigateurs interrogent ce point same-origin. Le cache de réponse CDN
// mutualise les lectures entre visiteurs et ce petit cache en mémoire déduplique
// aussi les requêtes qui arrivent ensemble sur une même instance Next.
//
// Une valeur expirée n'est jamais servie en secours : si Railway ne répond
// plus après les 120 secondes, la route rend une erreur non cachable. Le
// navigateur peut alors masquer ses agrégats sans inventer un succès.
const SHARED_TTL_MS = 120_000;
const SUCCESS_CACHE_CONTROL = "public, max-age=0, s-maxage=120, must-revalidate";

type PulseBody = Record<string, unknown>;
type CachedPulse = {
  body: PulseBody;
  checkedAt: number;
  expiresAt: number;
};

let cachedPulse: CachedPulse | null = null;
let pendingPulse: Promise<CachedPulse> | null = null;

export const dynamic = "force-dynamic";

function isPulseBody(value: unknown): value is PulseBody {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const body = value as PulseBody;
  if (body.live !== true && body.live !== false) return false;
  if (body.live === false) return true;
  return (
    (typeof body.last_reading === "string" || body.last_reading === null)
    && typeof body.readings_24h === "number"
    && Number.isSafeInteger(body.readings_24h)
    && body.readings_24h >= 0
    && typeof body.drops_24h === "number"
    && Number.isSafeInteger(body.drops_24h)
    && body.drops_24h >= 0
  );
}

async function readRailwayPulse(): Promise<CachedPulse> {
  const response = await fetch(`${API}/api/catalog/pulse`, {
    // Le partage est piloté ici et par le cache CDN de cette route. On ne
    // dépend pas du cache ISR, qui pourrait resservir une valeur périmée
    // pendant qu'une revalidation en panne tourne en arrière-plan.
    cache: "no-store",
    headers: { accept: "application/json" },
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error(`Pulse upstream HTTP ${response.status}`);

  const body: unknown = await response.json();
  if (!isPulseBody(body)) throw new Error("Pulse upstream contract invalid");

  const checkedAt = Date.now();
  return { body, checkedAt, expiresAt: checkedAt + SHARED_TTL_MS };
}

async function sharedPulse(): Promise<CachedPulse> {
  const now = Date.now();
  if (cachedPulse && cachedPulse.expiresAt > now) return cachedPulse;

  if (!pendingPulse) {
    pendingPulse = readRailwayPulse()
      .then((next) => {
        cachedPulse = next;
        return next;
      })
      .finally(() => {
        pendingPulse = null;
      });
  }
  return pendingPulse;
}

export async function GET() {
  try {
    const pulse = await sharedPulse();
    return NextResponse.json(
      {
        ...pulse.body,
        // Ce temps appartient à la lecture Railway, pas à la requête du
        // navigateur. Il empêche un cache intermédiaire de rajeunir les
        // compteurs à chaque poll.
        proxy_checked_at: new Date(pulse.checkedAt).toISOString(),
      },
      { headers: { "Cache-Control": SUCCESS_CACHE_CONTROL } },
    );
  } catch {
    return NextResponse.json(
      { error: "pulse_unavailable" },
      {
        status: 502,
        headers: { "Cache-Control": "no-store" },
      },
    );
  }
}
