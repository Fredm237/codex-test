"use client";

// Les rangées vivantes du catalogue.
//
// Je les avais supprimées en reconstruisant la page, et c'était une erreur :
// ce sont elles qui font qu'un catalogue paraît vivant. Une grille de 48
// produits triés par pertinence ne raconte rien ; « les prix qui ont reculé
// aujourd'hui » raconte que quelque chose bouge, et le contenu change tout
// seul d'un jour à l'autre.
//
// Elles s'affichent uniquement sur la racine du catalogue : sous un filtre,
// elles parleraient d'autre chose que ce qui est demandé.

import { useEffect, useRef } from "react";
import { ProductCard } from "./ProductCard";
import type { CardOffer } from "./ProductCard";
import { useLocale } from "@/lib/i18n";

export type RailSection = { key: string; items: CardOffer[] };

// Clés de dictionnaire : les rangées doivent se lire en NL et en EN.
const TITLES: Record<string, [string, string]> = {
  drops: ["rail.dropsT", "rail.dropsS"],
  lowest: ["rail.lowestT", "rail.lowestS"],
  budget: ["rail.budgetT", "rail.budgetS"],
  fresh: ["rail.freshT", "rail.freshS"],
};

/** Apparition en cascade à l'entrée dans le champ de vision.
 *  Le mouvement porte une information — l'ordre de lecture — plutôt que de
 *  décorer. Réglage système respecté : tout apparaît d'un coup si l'animation
 *  est refusée. */
function useStagger<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      root.classList.add("shown");
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("shown");
          io.unobserve(entry.target);
        }
      },
      { threshold: 0.15 }
    );
    io.observe(root);
    return () => io.disconnect();
  }, []);
  return ref;
}

function Rail({ section }: { section: RailSection }) {
  const { t } = useLocale();
  const keys = TITLES[section.key];
  const ref = useStagger<HTMLElement>();
  if (!keys || section.items.length === 0) return null;

  return (
    <section className="fx-rail fx-stagger" ref={ref}>
      <header className="fx-rail-head">
        <h2 className="fx-h2 fx-rail-title">{t(keys[0])}</h2>
        <p className="fx-fine">{t(keys[1])}</p>
      </header>
      <div className="fx-rail-scroll">
        {section.items.map((offer, i) => (
          <div
            className="fx-rail-item"
            key={`${section.key}-${offer.id}`}
            style={{ ["--i" as string]: i }}
          >
            <ProductCard offer={offer} />
          </div>
        ))}
      </div>
    </section>
  );
}

export function Rails({ sections }: { sections: RailSection[] }) {
  if (!sections.length) return null;
  return (
    <div className="fx-rails">
      {sections.map((s) => (
        <Rail section={s} key={s.key} />
      ))}
    </div>
  );
}
