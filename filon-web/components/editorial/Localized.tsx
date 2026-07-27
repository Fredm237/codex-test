"use client";

import type { ReactNode } from "react";
import { useLocale } from "@/lib/i18n";

/**
 * Choisit le corps FR, NL ou EN selon la langue active. Permet de garder les
 * pages en composants serveur (export `metadata`) tout en offrant un contenu
 * multilingue. `en` est optionnel : à défaut, on retombe sur `fr`.
 */
export function Localized({ fr, nl, en }: { fr: ReactNode; nl: ReactNode; en?: ReactNode }) {
  const { locale } = useLocale();
  if (locale === "nl") return <>{nl}</>;
  if (locale === "en") return <>{en ?? fr}</>;
  return <>{fr}</>;
}
