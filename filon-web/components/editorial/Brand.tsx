import Link from "next/link";
import type { MouseEventHandler } from "react";
export function BrandMark({ size = 30 }: { size?: number }) {
 return <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false"><path d="M4 4h24v7H12v5h12v7H12v5H4Z" fill="currentColor" /></svg>;
}
export function BrandLogo({ as = "a", href = "/", className = "", onClick, markSize = 26 }: { as?: "a" | "span"; href?: string; className?: string; onClick?: MouseEventHandler; markSize?: number }) {
 const inner = <><BrandMark size={markSize} /><span>filon<span className="fn-brand-dot">®</span></span></>;
 return as === "span" ? <span className={`fn-brand ${className}`}>{inner}</span> : <Link className={`fn-brand ${className}`} href={href} onClick={onClick} aria-label="FILON — Accueil">{inner}</Link>;
}
