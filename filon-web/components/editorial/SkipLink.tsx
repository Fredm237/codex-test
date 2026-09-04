"use client";

import type { MouseEvent, ReactNode } from "react";

export function SkipLink({
  targetId,
  className,
  children,
}: {
  targetId: string;
  className?: string;
  children: ReactNode;
}) {
  const activate = (event: MouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById(targetId);
    if (!target) return;
    event.preventDefault();
    target.focus({ preventScroll: true });
    target.scrollIntoView({ block: "start" });
    window.history.pushState(null, "", `#${targetId}`);
  };

  return (
    <a className={className} href={`#${targetId}`} onClick={activate}>
      {children}
    </a>
  );
}
