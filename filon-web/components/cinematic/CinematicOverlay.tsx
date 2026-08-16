"use client";

import { HeroSearch } from "@/components/filon/HeroSearch";
import type { Locale, TimelineState } from "./types";

type Props = {
  locale: Locale;
  timeline: TimelineState;
  onSkip: () => void;
};

const copy = {
  fr: { skip: "Passer l’introduction", scroll: "Faites avancer la scène", observed: "6,98 € · Babubas", alternative: "6,99 € · Bazta", availability: "Disponibles dans le dernier flux", score: "Score FILON : prix, marchand, disponibilité" },
  nl: { skip: "Intro overslaan", scroll: "Beweeg door de scène", observed: "€ 6,98 · Babubas", alternative: "€ 6,99 · Bazta", availability: "Beschikbaar in de laatste feed", score: "FILON-score: prijs, verkoper, beschikbaarheid" },
  en: { skip: "Skip introduction", scroll: "Move through the scene", observed: "€6.98 · Babubas", alternative: "€6.99 · Bazta", availability: "Available in the latest feed", score: "FILON Score: price, merchant, availability" },
} satisfies Record<Locale, Record<string, string>>;

export function CinematicOverlay({ locale, timeline, onSkip }: Props) {
  const text = copy[locale];
  const fragment = timeline.shot.copy[locale];
  const focus = timeline.shot.focus;
  const showProofs = focus === "compare" || focus === "opportunity" || focus === "intelligence" || focus === "score" || focus === "decision";

  return (
    <div className={`ce-overlay ce-focus-${focus}`}>
      <button className="ce-skip" type="button" onClick={onSkip}>{text.skip}</button>

      <div className="ce-copy" style={{ opacity: timeline.overlayOpacity }}>
        {fragment.eyebrow && <p>{fragment.eyebrow}</p>}
        <h1>{fragment.title}</h1>
        {fragment.detail && <small>{fragment.detail}</small>}
        {fragment.cta && <a href={fragment.cta.href} className="ce-cta">{fragment.cta.label}</a>}
      </div>

      {showProofs && (
        <div className="ce-proof-line" style={{ opacity: Math.min(1, timeline.overlayOpacity * 1.18) }} aria-label="Éléments de comparaison observés">
          {focus === "score" ? <span>{text.score}</span> : <><span>{text.observed}</span><i /> <span>{text.alternative}</span>{focus === "intelligence" && <><i /> <span>{text.availability}</span></>}</>}
        </div>
      )}

      <div className="ce-search"><HeroSearch /></div>
      {focus === "arrival" && <p className="ce-scroll-hint">{text.scroll}</p>}
    </div>
  );
}
