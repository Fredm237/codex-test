import type { ReactNode, CSSProperties } from "react";

type Variant = "primary" | "ghost";

const base: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  fontFamily: "inherit",
  fontSize: 15,
  fontWeight: 600,
  letterSpacing: "-0.01em",
  padding: "13px 24px",
  borderRadius: "var(--r-full)",
  border: "1px solid transparent",
  cursor: "pointer",
  transition: "transform .18s var(--ease-out), box-shadow .25s, background .2s, border-color .2s",
  whiteSpace: "nowrap",
};

const variants: Record<Variant, CSSProperties> = {
  primary: {
    color: "#05121f",
    background: "var(--vein)",
    boxShadow: "var(--shadow-glow)",
  },
  ghost: {
    color: "var(--text)",
    background: "var(--surface)",
    borderColor: "var(--border-2)",
  },
};

export function Button({
  children,
  href,
  variant = "primary",
  style,
}: {
  children: ReactNode;
  href: string;
  variant?: Variant;
  style?: CSSProperties;
}) {
  return (
    <a href={href} className="filon-btn" style={{ ...base, ...variants[variant], ...style }}>
      {children}
    </a>
  );
}
