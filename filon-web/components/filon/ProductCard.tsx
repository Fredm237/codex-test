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

import { useCallback, useState } from "react";
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
  /** État déclaré par le dernier flux marchand ; jamais une promesse de livraison. */
  in_stock?: boolean | null;
  /** Date du dernier relevé de prix Core, distincte d’une mise à jour interne. */
  observed_at?: string | null;
  drop_pct?: number;
  price_high?: number | null;
  is_lowest?: boolean;
};

export function ProductCard({
  offer,
  copy,
  href,
  showEvidence = false,
}: {
  offer: CardOffer;
  /** Facultatif : sans lui, la carte lit la langue courante elle-même. Les
   *  pages serveur n'ont donc rien à transmettre, et ne peuvent plus figer le
   *  français par mégarde. */
  copy?: CardCopy;
  href?: string;
  /** Active les preuves du dernier flux dans les grilles de comparaison. */
  showEvidence?: boolean;
}) {
  const { locale } = useLocale();
  const words = copy ?? CARD_COPY[locale];
  const drop = offer.drop_pct && offer.drop_pct >= 1 ? Math.round(offer.drop_pct) : null;
  const target = href ?? `/produit/${offer.id}/`;
  const availability = offer.in_stock === true
    ? { label: words.available, state: "available" }
    : offer.in_stock === false
      ? { label: words.unavailable, state: "unavailable" }
      : { label: words.availabilityUnknown, state: "unknown" };
  const observed = (() => {
    const timestamp = offer.observed_at ? Date.parse(offer.observed_at) : Number.NaN;
    if (!Number.isFinite(timestamp)) return { label: words.observationUnavailable, state: "unknown" };
    const ageDays = Math.max(0, Math.floor((Date.now() - timestamp) / 86_400_000));
    if (ageDays === 0) return { label: words.observedToday, state: "fresh" };
    if (ageDays === 1) return { label: words.observedYesterday, state: "fresh" };
    if (ageDays < 7) return { label: words.observedDays(ageDays), state: "recent" };
    const dateLocale = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
    return {
      label: words.observedOn(new Intl.DateTimeFormat(dateLocale, { day: "numeric", month: "short" }).format(new Date(timestamp))),
      state: "old",
    };
  })();
  // Les flux marchands livrent régulièrement des URL d'images mortes. Sans ce
  // repli, la carte affichait un cadre vide sans rien expliquer.
  const [imageOk, setImageOk] = useState(true);
  const [imageLoaded, setImageLoaded] = useState(false);
  // Si le navigateur a terminé l'image avant l'hydratation, `onLoad` ne se
  // déclenche plus. Le ref rend alors immédiatement le visuel réel.
  const imageRef = useCallback((node: HTMLImageElement | null) => {
    if (node?.complete && node.naturalWidth > 0) setImageLoaded(true);
  }, []);

  return (
    <motion.article
      className="fx-product"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
    >
      <div className={`fx-product-media${offer.image && imageOk && !imageLoaded ? " is-loading" : ""}`}>
        {offer.image && imageOk ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            ref={imageRef}
            src={offer.image}
            alt=""
            loading="lazy"
            decoding="async"
            onLoad={() => setImageLoaded(true)}
            onError={() => { setImageOk(false); setImageLoaded(false); }}
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

        {showEvidence && (
          <div className="fx-product-evidence-stack" aria-label={`${availability.label}. ${observed.label}.`}>
            <span className={`fx-product-evidence is-${availability.state}`}>
              <span className="fx-product-evidence-dot" aria-hidden="true" />
              {availability.label}
            </span>
            <span className={`fx-product-evidence is-${observed.state}`}>
              <span className="fx-product-evidence-dot" aria-hidden="true" />
              {observed.label}
            </span>
          </div>
        )}

        <div className="fx-product-foot">
          <span className="fx-product-price">
            <b>{money(offer.price, offer.currency, locale)}</b>
            {drop && offer.price_high != null && <s>{money(offer.price_high, offer.currency, locale)}</s>}
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
