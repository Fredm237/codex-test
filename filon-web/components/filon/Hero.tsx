"use client";

// Hero — fond sombre béton, titre ambre, barre de recherche.
// Pas de vidéo : la séquence scrubée qui suit EST l'expérience.
// Le Hero pose la question, la séquence la joue.

import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

export function Hero({ proof }: { proof: Proof | null }) {
  const { t } = useLocale();

  return (
    <section className="fx-hero">
      {/* Contenu centré */}
      <div className="fx-hero-content">
        <motion.h1
          className="fx-hero-title"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          {t("hero.l1")} {t("hero.l2")} <em>{t("hero.l3")}</em>
        </motion.h1>

        <motion.div
          className="fx-hero-search-wrap"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <HeroSearch />
        </motion.div>
      </div>
    </section>
  );
}
