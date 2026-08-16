"use client";

import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const COPY = {
  fr: {
    eyebrow: "Le copilote d’achat belge",
    title: "Est-ce vraiment le\nbon prix ?",
    body: "FILON compare les offres réellement observées et vous montre ce que nous savons avant votre décision.",
    film: "Voir le film",
    signal: "Prix, marchands et disponibilités observés",
  },
  nl: {
    eyebrow: "De Belgische koopcopiloot",
    title: "Is dit echt de\njuiste prijs?",
    body: "FILON vergelijkt werkelijk waargenomen aanbiedingen en toont wat we weten vóór je beslist.",
    film: "Bekijk de film",
    signal: "Waargenomen prijzen, winkels en beschikbaarheid",
  },
  en: {
    eyebrow: "The Belgian shopping copilot",
    title: "Is this really the\nright price?",
    body: "FILON compares genuinely observed offers and shows what we know before you decide.",
    film: "Watch the film",
    signal: "Observed prices, merchants and availability",
  },
} as const;

/**
 * Accueil clair, intentionnel et léger : une image dédiée par format plutôt
 * qu’un long flux de frames sombre. Le film intégral reste volontaire et se
 * lance depuis l’assistant ; il ne pénalise jamais le premier écran mobile.
 */
export function ImmersiveExperience() {
  const { locale } = useLocale();
  const copy = COPY[locale] ?? COPY.fr;

  return (
    <section className="fx-light-home">
      <picture>
        <source media="(max-width: 768px)" srcSet="/film/filon-home-mobile.jpg" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="fx-light-home-image" src="/film/filon-home-desktop.jpg" alt="" aria-hidden="true" fetchPriority="high" />
      </picture>
      <div className="fx-light-home-wash" aria-hidden="true" />
      <div className="fx-light-home-content">
        <p className="fx-light-home-eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="fx-light-home-body">{copy.body}</p>
        <div className="fx-light-home-actions">
          <a className="fx-light-home-film" href="/recherche?film=1"><span aria-hidden="true">▶</span>{copy.film}</a>
        </div>
        <div className="fx-light-home-search"><HeroSearch /></div>
        <p className="fx-light-home-signal"><span aria-hidden="true" />{copy.signal}</p>
      </div>
    </section>
  );
}
