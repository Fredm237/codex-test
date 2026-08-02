"use client";

// Hero — Vidéo 3D en fond plein écran.
// Le titre et la recherche flottent par-dessus.
// Minimum de texte. Maximum d'impact visuel.

import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

export function Hero({ proof }: { proof: Proof | null }) {
  const { t } = useLocale();

  return (
    <section className="fx-hero">
      {/* Vidéo 3D en fond — plein écran */}
      <video
        className="fx-hero-bg-video"
        autoPlay
        muted
        loop
        playsInline
        poster="/img/closing-bg.png"
      >
        <source src="/video/filon_hf_promo.mp4" type="video/mp4" />
      </video>

      {/* Overlay sombre pour lisibilité */}
      <div className="fx-hero-overlay" aria-hidden="true" />

      {/* Contenu centré par-dessus */}
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
