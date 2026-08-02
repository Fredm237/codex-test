"use client";

// Hero — Refonte TOTALE inspirée de Phia.com.
//
// Structure Phia :
// 1. Titre centré, GRAND, serif, avec un mot en italique
// 2. Sous-titre d'une ligne, centré
// 3. Image dominante (>60% de la hauteur du viewport)
// 4. Logos presse ou stats en bandeau en bas
//
// Pas de grille 2 colonnes. Pas de carte à côté. Le titre EST le hero.

import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";
import dynamic from "next/dynamic";

const OrbViewer3D = dynamic(() => import("./OrbViewer3D").then(m => ({ default: m.OrbViewer3D })), { ssr: false });

function money(value: number, currency: string): string {
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${value.toLocaleString("fr-BE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}

export function Hero({ proof }: { proof: Proof | null }) {
  const { t, locale } = useLocale();
  const tag = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const product = proof?.product ?? null;
  const stats = proof?.stats ?? null;

  return (
    <section className="fx-hero">
      <div className="fx-hero-inner">
        {/* Titre centré — comme Phia "Never Overpay Again" */}
        <motion.div
          className="fx-hero-headline"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="fx-hero-title">
            {t("hero.l1")} {t("hero.l2")} <em>{t("hero.l3")}</em>
          </h1>
          <p className="fx-hero-subtitle">
            {t("hero.ledeA")} {stats ? stats.merchants.toLocaleString(tag) : "150+"} {t("hero.ledeB")}
          </p>
        </motion.div>

        {/* Barre de recherche centrée */}
        <motion.div
          className="fx-hero-search-wrap"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <HeroSearch />
        </motion.div>

        {/* Image dominante avec carte produit flottante — comme Phia */}
        {/* Orbe 3D interactif — flotte et réagit au curseur */}
        <motion.div
          className="fx-hero-visual"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <OrbViewer3D />
        </motion.div>

        {product && (
          <motion.div
            className="fx-hero-float-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="fx-hero-image-wrap">
              {/* Carte produit flottante sur l'image — comme Phia */}
              <article className="fx-hero-float-card">
                {product.image && (
                  <img src={product.image} alt="" width={56} height={56} className="fx-hero-float-thumb" />
                )}
                <div className="fx-hero-float-info">
                  {product.brand && <span className="fx-hero-float-brand">{product.brand}</span>}
                  <span className="fx-hero-float-name">{product.name}</span>
                  <span className="fx-hero-float-price">
                    <b>{money(product.priceMin, product.currency)}</b>
                    <s>{money(product.priceMax, product.currency)}</s>
                  </span>
                </div>
              </article>
            </div>
          </motion.div>
        )}

        {/* Stats en bandeau — comme les logos presse chez Phia */}
        {stats && (
          <motion.div
            className="fx-hero-stats"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            <span><b>{stats.offers.toLocaleString(tag)}</b> {t("hero.offersTracked")}</span>
            <span className="fx-hero-stats-sep" aria-hidden="true" />
            <span><b>{stats.multiMerchant.toLocaleString(tag)}</b> {t("hero.multiMerchant")}</span>
            <span className="fx-hero-stats-sep" aria-hidden="true" />
            <span><b>{stats.snapshots.toLocaleString(tag)}</b> {t("hero.snapshots")}</span>
          </motion.div>
        )}
      </div>
    </section>
  );
}
