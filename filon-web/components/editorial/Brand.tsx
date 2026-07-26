import type { MouseEventHandler } from "react";

/** Symbole FILON (tracés purs, net à toute taille). */
export function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg className="ed-brand-mark" width={size} height={size} viewBox="0 0 240 240" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="filon-mb" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#86D1B0" />
          <stop offset="1" stopColor="#8FB9E6" />
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="224" height="224" rx="49.28" fill="#26364B" />
      <g transform="translate(62,60) scale(1.16)">
        <g fill="none" stroke="url(#filon-mb)" strokeWidth="13" strokeLinecap="round" strokeLinejoin="round">
          <path d="M34 82 L34 20 L72 20" />
          <path d="M34 50 L60 50" />
        </g>
        <circle cx="72" cy="20" r="6.5" fill="#EF9F27" />
      </g>
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
