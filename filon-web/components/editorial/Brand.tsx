import type { MouseEventHandler } from "react";

/** Symbole FILON — VIVANT : le point doré pulse, le dégradé bouge. */
export function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg className="ed-brand-mark" width={size} height={size} viewBox="0 0 240 240" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="filon-mb" gradientUnits="userSpaceOnUse" x1="95" y1="166" x2="156" y2="78">
          <stop offset="0" stopColor="#86D1B0">
            <animate attributeName="stopColor" values="#86D1B0;#EF9F27;#8FB9E6;#86D1B0" dur="4s" repeatCount="indefinite" />
          </stop>
          <stop offset="1" stopColor="#8FB9E6">
            <animate attributeName="stopColor" values="#8FB9E6;#86D1B0;#EF9F27;#8FB9E6" dur="4s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
        <filter id="filon-glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect x="8" y="8" width="224" height="224" rx="49.28" fill="#26364B" />
      <g fill="none" stroke="url(#filon-mb)" strokeWidth="17" strokeLinecap="round" strokeLinejoin="round">
        <path d="M95 78 L95 166" />
        <path d="M95 78 L156 78" />
        <path d="M95 121 L145 121" />
      </g>
      <circle cx="156" cy="78" r="10.5" fill="#EF9F27" filter="url(#filon-glow)">
        <animate attributeName="r" values="10.5;13;10.5" dur="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="1;0.7;1" dur="2s" repeatCount="indefinite" />
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
