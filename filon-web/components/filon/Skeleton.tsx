"use client";

/**
 * Skeletons de chargement premium.
 * 
 * Pourquoi c'est important :
 * - Un skeleton bien fait donne l'impression que le site est rapide
 * - L'animation "shimmer" (vague lumineuse) crée une sensation de vie
 * - Les proportions réalistes évitent le "layout shift" au chargement
 * 
 * Inspiré de Phia.com : les skeletons sont subtils, avec un shimmer
 * très doux (pas un flash agressif) et des coins arrondis cohérents
 * avec le design system.
 */

import type { CSSProperties } from "react";

function Bone({
  width,
  height,
  radius,
  className = "",
  style,
}: {
  width?: string | number;
  height?: string | number;
  radius?: string;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={`fx-skeleton ${className}`}
      style={{
        width: width ?? "100%",
        height: height ?? 16,
        borderRadius: radius ?? "var(--fx-radius-xs)",
        ...style,
      }}
      aria-hidden="true"
    />
  );
}

/** Skeleton d'une carte produit — même proportions que ProductCard */
export function ProductCardSkeleton() {
  return (
    <div className="fx-product fx-skeleton-card" aria-hidden="true">
      <div className="fx-product-media">
        <Bone width="100%" height="100%" radius="0" />
      </div>
      <div className="fx-product-body">
        <Bone width="40%" height={10} />
        <Bone width="85%" height={14} style={{ marginTop: 8 }} />
        <Bone width="60%" height={14} style={{ marginTop: 4 }} />
        <Bone width="30%" height={12} style={{ marginTop: 8 }} />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "auto", paddingTop: 12 }}>
          <Bone width="35%" height={18} />
          <Bone width={80} height={36} radius="var(--fx-radius-full)" />
        </div>
      </div>
    </div>
  );
}

/** Grille de skeletons produits */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="fx-product-grid" aria-busy="true" aria-label="Chargement des produits">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** Skeleton pour le verdict FILON */
export function VerdictSkeleton() {
  return (
    <div className="fx-skeleton-verdict" aria-hidden="true">
      <Bone width={120} height={12} />
      <Bone width="70%" height={20} style={{ marginTop: 12 }} />
      <Bone width="90%" height={14} style={{ marginTop: 10 }} />
      <Bone width="80%" height={14} style={{ marginTop: 6 }} />
      <Bone width="50%" height={12} style={{ marginTop: 12 }} />
    </div>
  );
}

/** Skeleton pour une ligne d'offre */
export function OfferRowSkeleton() {
  return (
    <div className="fx-skeleton-offer" aria-hidden="true">
      <Bone width="30%" height={16} />
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <Bone width={70} height={18} />
        <Bone width={60} height={14} />
        <Bone width={60} height={36} radius="var(--fx-radius-full)" />
      </div>
    </div>
  );
}

export { Bone };
