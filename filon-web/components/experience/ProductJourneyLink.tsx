"use client";

import Link from "next/link";
import type { MouseEvent, ReactNode } from "react";

export const PRODUCT_JOURNEY_EVENT = "filon:product-journey";

export type ProductJourneyDetail = {
  image: string;
  label: string;
  source: { height: number; left: number; top: number; width: number };
};

type Props = {
  children: ReactNode;
  className?: string;
  href: string;
  image?: string | null;
  label: string;
};

/**
 * Transporte l'objet observé jusqu'au chapitre produit. Le lien reste un lien
 * Next normal : sans JS, sans image ou en mouvement réduit, la navigation
 * continue simplement sans couche cinématique.
 */
export function ProductJourneyLink({ children, className, href, image, label }: Props) {
  const beginJourney = (event: MouseEvent<HTMLAnchorElement>) => {
    if (
      event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
      || window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) return;

    const scope = event.currentTarget.closest("[data-product-transition-source], article, aside, section");
    const sourceImage = scope?.querySelector("img");
    const sourceUrl = image || sourceImage?.currentSrc || sourceImage?.getAttribute("src");
    if (!sourceUrl) return;
    const rect = (sourceImage ?? event.currentTarget).getBoundingClientRect();
    window.dispatchEvent(new CustomEvent<ProductJourneyDetail>(PRODUCT_JOURNEY_EVENT, {
      detail: {
        image: sourceUrl,
        label,
        source: { height: rect.height, left: rect.left, top: rect.top, width: rect.width },
      },
    }));
  };

  return <Link className={className} href={href} onClick={beginJourney}>{children}</Link>;
}
