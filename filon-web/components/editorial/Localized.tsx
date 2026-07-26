"use client";

import type { ReactNode } from "react";
import { useLocale } from "@/lib/i18n";

/**
 * Choisit le corps FR ou NL selon la langue active. Permet de garder les pages
 * en composants serveur (export `metadata`) tout en offrant un contenu bilingue.
 */
export function Localized({ fr, nl }: { fr: ReactNode; nl: ReactNode }) {
  const { locale } = useLocale();
  return <>{locale === "nl" ? nl : fr}</>;
}
