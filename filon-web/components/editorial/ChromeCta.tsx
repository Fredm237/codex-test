import type { ReactNode } from "react";

/** Logo Google Chrome, reconstruit en SVG (net à toute taille, aucun fichier à héberger). */
export function ChromeMark({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
      focusable="false"
      style={{ display: "block", flex: "none" }}
    >
      <path fill="#EA4335" d="M24 24 6.68 14A20 20 0 0 1 41.32 14Z" />
      <path fill="#FBBC05" d="M24 24 41.32 14A20 20 0 0 1 24 44Z" />
      <path fill="#34A853" d="M24 24 24 44A20 20 0 0 1 6.68 14Z" />
      <circle cx="24" cy="24" r="11" fill="#fff" />
      <circle cx="24" cy="24" r="8.4" fill="#1A73E8" />
    </svg>
  );
}

/**
 * Bouton « Ajouter à Chrome » avec le logo officiel.
 * `variant` mappe sur les styles d'`ed-btn` existants (ghost, ghostlight, wave…).
 */
export function ChromeCta({
  variant = "ghost",
  href = "/#installer",
  label = "Ajouter à Chrome",
  size = 20,
  style,
}: {
  variant?: string;
  href?: string;
  label?: ReactNode;
  size?: number;
  style?: React.CSSProperties;
}) {
  return (
    <a className={`ed-btn ${variant} ed-chrome-cta`} href={href} style={style}>
      <ChromeMark size={size} />
      <span>{label}</span>
    </a>
  );
}
