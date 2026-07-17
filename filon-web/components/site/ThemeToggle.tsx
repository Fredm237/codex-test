"use client";

import { useCallback } from "react";

export function ThemeToggle() {
  const toggle = useCallback(() => {
    const root = document.documentElement;
    const current = root.getAttribute("data-theme");
    const isDark = current ? current === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem("filon-theme", next);
    } catch {
      /* storage may be unavailable */
    }
  }, []);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Changer de thème clair ou sombre"
      style={{
        width: 40,
        height: 40,
        display: "grid",
        placeItems: "center",
        borderRadius: "var(--r-full)",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        color: "var(--text-dim)",
        cursor: "pointer",
      }}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
      </svg>
    </button>
  );
}
