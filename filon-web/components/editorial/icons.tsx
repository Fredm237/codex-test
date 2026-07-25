import type { ReactNode } from "react";

/**
 * Petites icônes « ligne » sobres (currentColor), pensées pour remplacer les
 * émojis dans les grilles et sections. Trait fin, style premium, cohérent.
 */
function I({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {children}
    </svg>
  );
}

export const IcLock = () => <I><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 018 0v3" /></I>;
export const IcNoResale = () => <I><circle cx="12" cy="12" r="8.5" /><path d="M6 6l12 12" /></I>;
export const IcEncrypted = () => <I><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 018 0v3" /><path d="M12 15v2" /></I>;
export const IcShieldCheck = () => <I><path d="M12 3l7 3v5c0 4.2-2.9 7.6-7 9-4.1-1.4-7-4.8-7-9V6z" /><path d="M9 12l2 2 4-4.5" /></I>;
export const IcChartNoCookie = () => <I><path d="M4 20V4" /><path d="M4 20h16" /><rect x="8" y="12" width="3" height="5" /><rect x="13" y="8" width="3" height="9" /></I>;
export const IcEye = () => <I><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" /><circle cx="12" cy="12" r="2.6" /></I>;
export const IcChat = () => <I><path d="M4 5h16v11H9l-4 3.5V16H4z" /><path d="M8 9.5h8M8 12.5h5" /></I>;
export const IcHeart = () => <I><path d="M12 20s-7-4.3-9-9.2C1.8 7.7 3.6 5 6.4 5c1.9 0 3.1 1.1 3.9 2.3.8-1.2 2-2.3 3.9-2.3 2.8 0 4.6 2.7 3.4 5.8C19 15.7 12 20 12 20z" /></I>;
export const IcSpark = () => <I><path d="M12 4l1.6 4.8L18 10l-4.4 1.2L12 16l-1.6-4.8L6 10l4.4-1.2z" /></I>;
