"use client";

// La carte produit — une seule, partagée par les rails, la grille du
// catalogue et les pages rayon. Trois surfaces en avaient chacune une variante :
// une correction du prix, du badge ou de la cible tactile devait être faite
// trois fois, et ne l'était pas.
//
// Trois défauts de l'ancienne carte sont corrigés ici :
//
// - la seule action visible mesurait 12 px de texte dans une pastille de 30 px,
//   sous le minimum tactile de 44 px ;
// - elle n'apparaissait qu'au survol, donc n'existait pas sur un écran tactile ;
// - le lien vers la fiche ne couvrait que le titre et l'image, jamais la carte.
//
// La carte entière est désormais cliquable (lien étiré depuis le titre), et le
// lien marchand reste distinct, au-dessus, avec sa propre cible.

import { useState } from "react";
import { motion } from "framer-motion";
import { CARD_COPY, money, type CardCopy } from "./product-copy";
import { useLocale } from "@/lib/i18n";

export type CardOffer = {
  id: number;
  name: string;
  brand?: string | null;
  price?: number | null;
  currency?: string | null;
  image?: string | null;
  link?: string | null;
  merchant?: { name: string; slug: string } | null;
  drop_pct?: number;
  price_high?: number | null;
  is_lowest?: boolean;
};

export function ProductCard({
  offer,
  copy,
  href,
}: {
  offer: CardOffer;
  /** Facultatif : sans lui, la carte lit la langue courante elle-même. Les
   *  pages serveur n'ont donc rien à transmettre, et ne peuvent plus figer le
   *  français par mégarde. */
  copy?: CardCopy;
  href?: string;
}) {
  const { locale } = useLocale();
  const words = copy ?? CARD_COPY[locale];
  const drop = offer.drop_pct && offer.drop_pct >= 1 ? Math.round(offer.drop_pct) : null;
  const target = href ?? `/produit/${offer.id}/`;
  // Les flux marchands livrent régulièrement des URL d'images mortes. Sans ce
  // repli, la carte affichait un cadre vide sans rien expliquer.
  const [imageOk, setImageOk] = useState(true);

  return (
    <motion.article
      className="fx-product"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
    >
      <div className="fx-product-media">
        {offer.image && imageOk ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={offer.image}
            alt=""
            loading="lazy"
            decoding="async"
            onError={() => setImageOk(false)}
          />
        ) : (
          <span className="fx-product-noimage">{words.noImage}</span>
        )}
        {(drop || offer.is_lowest) && (
          <span className="fx-product-badges">
            {drop && <span className="fx-badge gain">−{drop}&nbsp;%</span>}
            {offer.is_lowest && <span className="fx-badge brand">{words.lowest}</span>}
          </span>
        )}
      </div>

      <div className="fx-product-body">
        {offer.brand && <span className="fx-product-brand">{offer.brand}</span>}

        {/* Lien étiré : toute la carte devient la cible, sans imbriquer
            d'ancres l'une dans l'autre (ce qui serait invalide). */}
        <a className="fx-product-name" href={target}>
          {offer.name}
        </a>

        {offer.merchant && (
          <span className="fx-product-merchant">
            {words.at} {offer.merchant.name}
          </span>
        )}

        <div className="fx-product-foot">
          <span className="fx-product-price">
            <b>{money(offer.price, offer.currency)}</b>
            {drop && offer.price_high != null && <s>{money(offer.price_high, offer.currency)}</s>}
          </span>

          {offer.link && (
            <a
              className="fx-product-cta"
              href={offer.link}
              target="_blank"
              rel="noopener noreferrer sponsored"
            >
              {words.see}
            </a>
          )}
        </div>
      </div>
    </motion.article>
  );
}
