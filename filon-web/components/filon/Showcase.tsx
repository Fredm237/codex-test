"use client";

// Trois démonstrations, chacune posée sur une photo de vie.
//
// C'est le dispositif central de la page d'accueil de Phia, et le rapport
// d'analyse le montre bien mieux que sa propre section « animations » ne
// l'explique. Phia n'écrit jamais « nous trouvons le meilleur prix » tout
// court : la phrase est accompagnée d'une photo d'une personne, sur laquelle
// flotte une carte montrant un article nommé, avec sa marque et son prix —
// « Aritzia · The Lodge Pant · 82 $ ». La promesse et sa preuve sont dans le
// même bloc visuel.
//
// Ce qui rend cela vivant tient en deux choses, et aucune n'est une animation :
//
//   1. un être humain est présent, dans une scène ordinaire ;
//   2. l'affirmation est immédiatement gagée sur un objet réel et nommé.
//
// Ici les cartes viennent du catalogue FILON. Aucune n'est composée pour la
// démonstration : si le catalogue est injoignable, la section entière
// disparaît plutôt que d'afficher un exemple inventé — c'est précisément
// l'erreur que la bande de preuves faisait avant la refonte.

import { useEffect, useRef } from "react";
import { useLocale } from "@/lib/i18n";
import { money } from "./product-copy";

export type ShowcaseItem = {
  id: number;
  name: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  image: string | null;
  price_high?: number | null;
  drop_pct?: number;
  merchant?: { name: string; slug: string } | null;
};

type Panel = {
  photo: string;
  titleKey: string;
  emphasisKey: string;
  bodyKey: string;
  badgeKey: string;
};

// Photos déjà présentes dans le dépôt : des scènes ordinaires, pas des visuels
// de banque d'images génériques.
const PANELS: Panel[] = [
  {
    photo: "/img/section-price.png",
    titleKey: "show.t1",
    emphasisKey: "show.e1",
    bodyKey: "show.b1",
    badgeKey: "show.badge1",
  },
  {
    photo: "/img/section-history.png",
    titleKey: "show.t2",
    emphasisKey: "show.e2",
    bodyKey: "show.b2",
    badgeKey: "show.badge2",
  },
  {
    photo: "/img/section-verdict.png",
    titleKey: "show.t3",
    emphasisKey: "show.e3",
    bodyKey: "show.b3",
    badgeKey: "show.badge3",
  },
];

/** Révélation à l'entrée dans le champ de vision, une seule fois.
 *  Le mouvement accompagne la lecture : il ne se rejoue pas au retour. */
function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      node.classList.add("shown");
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("shown");
        io.disconnect();
      },
      { threshold: 0.25 }
    );
    io.observe(node);
    return () => io.disconnect();
  }, []);
  return ref;
}

function ShowcasePanel({
  panel,
  item,
  flipped,
}: {
  panel: Panel;
  item: ShowcaseItem;
  flipped: boolean;
}) {
  const { t } = useLocale();
  const ref = useReveal<HTMLElement>();
  const drop = item.drop_pct && item.drop_pct >= 1 ? Math.round(item.drop_pct) : null;

  return (
    <section className={`fx-show${flipped ? " flipped" : ""}`} ref={ref}>
      <div className="fx-show-copy">
        <span className="fx-eyebrow brand">{t(panel.badgeKey)}</span>
        <h2 className="fx-h2 fx-show-title">
          {t(panel.titleKey)} <span className="it">{t(panel.emphasisKey)}</span>
        </h2>
        <p className="fx-body fx-show-body">{t(panel.bodyKey)}</p>
      </div>

      <div className="fx-show-stage">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="fx-show-photo" src={panel.photo} alt="" loading="lazy" decoding="async" />

        {/* La carte flotte sur la photo : l'objet est dans la scène, pas à côté. */}
        <article className="fx-show-card">
          {item.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img className="fx-show-thumb" src={item.image} alt="" loading="lazy" />
          )}
          <div className="fx-show-info">
            {item.brand && <span className="fx-show-brand">{item.brand}</span>}
            <a className="fx-show-name" href={`/produit/${item.id}/`}>
              {item.name}
            </a>
            <span className="fx-show-price">
              <b>{money(item.price, item.currency)}</b>
              {drop && item.price_high != null && (
                <s>{money(item.price_high, item.currency)}</s>
              )}
            </span>
          </div>
          {drop && <span className="fx-badge gain fx-show-tag">−{drop}&nbsp;%</span>}
        </article>
      </div>
    </section>
  );
}

export function Showcase({ items }: { items: ShowcaseItem[] }) {
  // Une démonstration sans objet réel n'en est pas une : on n'affiche que les
  // panneaux pour lesquels le catalogue a fourni un produit.
  const usable = items.filter((i) => i.price != null).slice(0, PANELS.length);
  if (usable.length === 0) return null;

  return (
    <div className="fx-shows">
      {usable.map((item, i) => (
        <ShowcasePanel key={item.id} panel={PANELS[i]} item={item} flipped={i % 2 === 1} />
      ))}
    </div>
  );
}
