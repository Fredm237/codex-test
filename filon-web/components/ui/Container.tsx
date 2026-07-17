import type { ReactNode } from "react";

export function Container({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }} className={className}>
      {children}
    </div>
  );
}
