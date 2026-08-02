// Géolocalisation : on dépose le pays et la langue devinés dans des cookies,
// sans jamais rediriger ni modifier l'URL.
//
// Le choix de ne pas rediriger est délibéré. Une redirection vers /fr ou /nl
// selon l'IP casse le partage de liens, brouille l'indexation, et enferme un
// néerlandophone de passage en France dans la mauvaise langue. Ici la
// détection ne fait que *proposer* : l'utilisateur garde la main, et son choix
// explicite l'emporte définitivement (voir LocaleProvider).
//
// L'en-tête de pays est posé par l'hébergeur (Vercel, Cloudflare). En local il
// est absent : on ne devine alors rien plutôt que d'inventer un pays.

import { NextResponse, type NextRequest } from "next/server";

const LOCALES = ["fr", "nl", "en"] as const;
type Locale = (typeof LOCALES)[number];

// Langue officielle majoritaire, par pays de diffusion de FILON. La Belgique
// est bilingue : le pays ne suffit pas à trancher, c'est la langue du
// navigateur qui départage (voir localeFromHeaders).
const COUNTRY_LOCALE: Record<string, Locale> = {
  BE: "fr",
  FR: "fr",
  LU: "fr",
  NL: "nl",
  CH: "fr",
};

/** Première langue acceptée par le navigateur qui soit une des nôtres. */
function localeFromAcceptLanguage(header: string | null): Locale | null {
  if (!header) return null;
  const ranked = header
    .split(",")
    .map((part) => {
      const [tag, q] = part.trim().split(";q=");
      return { tag: tag.trim().toLowerCase(), q: q ? Number(q) : 1 };
    })
    .sort((a, b) => b.q - a.q);
  for (const { tag } of ranked) {
    const base = tag.split("-")[0];
    if ((LOCALES as readonly string[]).includes(base)) return base as Locale;
  }
  return null;
}

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  const country = (
    request.headers.get("x-vercel-ip-country") ||
    request.headers.get("cf-ipcountry") ||
    ""
  ).toUpperCase();

  // La langue du navigateur prime sur le pays : elle dit ce que la personne
  // lit, là où l'IP ne dit que d'où elle se connecte. Un Belge néerlandophone
  // et un Belge francophone partagent le même pays.
  const guessed =
    localeFromAcceptLanguage(request.headers.get("accept-language")) ||
    COUNTRY_LOCALE[country] ||
    null;

  // Un an : ce sont des préférences, pas un suivi. Aucune donnée personnelle,
  // aucun identifiant — un code pays sur deux lettres et un code langue.
  const options = { path: "/", maxAge: 60 * 60 * 24 * 365, sameSite: "lax" as const };
  if (country) response.cookies.set("filon-country", country, options);
  if (guessed) response.cookies.set("filon-locale-guess", guessed, options);

  return response;
}

export const config = {
  // On évite les fichiers statiques et les images : la détection n'a de sens
  // que sur une page, et la faire tourner sur chaque asset coûterait cher.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
