import type { MouseEventHandler } from "react";

/** Symbole FILON — Refonte 2026.
 *  Doré, premium, vivant. Le F est en or avec un point qui pulse.
 *  Fond noir (comme le Hero), pas bleu marine.
 */
export function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg className="ed-brand-mark" width={size} height={size} viewBox="0 0 240 240" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="filon-gold" gradientUnits="userSpaceOnUse" x1="95" y1="166" x2="156" y2="78">
          <stop offset="0" stopColor="#D4A853">
            <animate attributeName="stopColor" values="#D4A853;#F5D78E;#C9963C;#D4A853" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="1" stopColor="#F5D78E">
            <animate attributeName="stopColor" values="#F5D78E;#C9963C;#D4A853;#F5D78E" dur="3s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
        <filter id="filon-glow">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {/* Fond noir — cohérent avec le Hero sombre */}
      <rect x="8" y="8" width="224" height="224" rx="49.28" fill="#0a0a0f" />
      {/* F doré */}
      <g fill="none" stroke="url(#filon-gold)" strokeWidth="17" strokeLinecap="round" strokeLinejoin="round">
        <path d="M95 78 L95 166" />
        <path d="M95 78 L156 78" />
        <path d="M95 121 L145 121" />
      </g>
      {/* Point doré qui pulse avec glow */}
      <circle cx="156" cy="78" r="10.5" fill="#EF9F27" filter="url(#filon-glow)">
        <animate attributeName="r" values="10.5;13.5;10.5" dur="2.5s" repeatCount="indefinite" />
        <animate attributeName="fill" values="#EF9F27;#F5D78E;#EF9F27" dur="2.5s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

/** Logo complet : symbole + « FILON ». Rendu en <a> (header) ou <span> (footer). */
export function BrandLogo({
  as = "a",
  href = "/",
  className = "",
  onClick,
  markSize = 30,
}: {
  as?: "a" | "span";
  href?: string;
  className?: string;
  onClick?: MouseEventHandler;
  markSize?: number;
}) {
  const inner = (
    <>
      <BrandMark size={markSize} />
      <span className="ed-brand-word">FILON</span>
    </>
  );
  if (as === "span") return <span className={`ed-brand ${className}`}>{inner}</span>;
  return (
    <a className={`ed-brand ${className}`} href={href} onClick={onClick}>
      {inner}
    </a>
  );
}
