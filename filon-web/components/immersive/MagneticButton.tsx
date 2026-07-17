"use client";

import { useRef, type ReactNode } from "react";

/** Button/link that is magnetically attracted to the cursor within its bounds. */
export function MagneticButton({
  children,
  href,
  className = "",
  strength = 0.4,
}: {
  children: ReactNode;
  href: string;
  className?: string;
  strength?: number;
}) {
  const ref = useRef<HTMLAnchorElement>(null);

  const onMove = (e: React.MouseEvent) => {
    const el = ref.current;
    if (!el || !window.matchMedia("(pointer:fine)").matches) return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left - r.width / 2) * strength;
    const y = (e.clientY - r.top - r.height / 2) * (strength + 0.15);
    el.style.transform = `translate(${x}px, ${y}px)`;
  };
  const reset = () => {
    if (ref.current) ref.current.style.transform = "";
  };

  return (
    <a
      ref={ref}
      href={href}
      className={className}
      data-hover
      onMouseMove={onMove}
      onMouseLeave={reset}
      style={{ transition: "transform 0.4s cubic-bezier(0.16,1,0.3,1)" }}
    >
      {children}
    </a>
  );
}
