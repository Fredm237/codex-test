"use client";

// Hero — Refonte visuelle spectaculaire 2026.
//
// Inspiré de Phia.com : chaque mot du titre apparaît individuellement avec un
// décalage, le fond a un gradient animé qui respire, et la carte produit flotte
// avec un léger effet parallax au mouvement de la souris.

import { motion, useMotionValue, useTransform, useSpring } from "framer-motion";
import { useEffect, useRef } from "react";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

function money(value: number, currency: string): string {
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${value.toLocaleString("fr-BE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}

/** Mot animé individuellement dans le titre. */
function Word({ children, delay }: { children: string; delay: number }) {
  return (
    <motion.span
      className="fx-hero-word"
      initial={{ opacity: 0, y: 40, rotateX: -40 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{
        delay,
        duration: 0.7,
        ease: [0.16, 1, 0.3, 1],
      }}
    >
      {children}
    </motion.span>
  );
}

/** Ligne du titre avec mots animés individuellement. */
function AnimatedLine({ text, startDelay }: { text: string; startDelay: number }) {
  const words = text.split(" ");
  return (
    <span className="fx-hero-line">
      {words.map((word, i) => (
        <Word key={i} delay={startDelay + i * 0.08}>
          {word}
        </Word>
      ))}
    </span>
  );
}

export function Hero({ proof }: { proof: Proof | null }) {
  const { t, locale } = useLocale();
  const tag = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const product = proof?.product ?? null;
  const stats = proof?.stats ?? null;

  // Parallax de la carte au mouvement de la souris
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 150, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 150, damping: 20 });
  const rotateX = useTransform(springY, [-0.5, 0.5], [6, -6]);
  const rotateY = useTransform(springX, [-0.5, 0.5], [-6, 6]);

  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const hero = heroRef.current;
    if (!hero) return;
    const handleMouse = (e: MouseEvent) => {
      const rect = hero.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      mouseX.set(x);
      mouseY.set(y);
    };
    hero.addEventListener("mousemove", handleMouse);
    return () => hero.removeEventListener("mousemove", handleMouse);
  }, [mouseX, mouseY]);

  return (
    <section className="fx-hero fx-hero-cinematic" ref={heroRef}>
      {/* Gradient animé en arrière-plan */}
      <div className="fx-hero-gradient" aria-hidden="true" />

      <div className="fx-container fx-hero-grid">
        <div className="fx-hero-copy">
          <motion.span
            className="fx-eyebrow brand"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {t("hero.eyebrowNew")}
          </motion.span>

          <h1 className="fx-display xl fx-hero-title fx-hero-title-cinematic">
            <AnimatedLine text={t("hero.l1")} startDelay={0.2} />
            <br />
            <AnimatedLine text={t("hero.l2")} startDelay={0.5} />
            <br />
            <span className="fx-hero-line it">
              <AnimatedLine text={t("hero.l3")} startDelay={0.8} />
            </span>
          </h1>

          <motion.p
            className="fx-lede fx-hero-lede"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            {t("hero.ledeA")} {stats ? stats.merchants.toLocaleString(tag) : t("hero.ledeOur")}{" "}
            {t("hero.ledeB")}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.4, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <HeroSearch />
          </motion.div>

          <motion.p
            className="fx-hero-actions"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6, duration: 0.5 }}
          >
            <a className="fx-hero-secondary" href="/catalogue/">
              {t("hero.explore")}
              <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                <path
                  d="M3 8h9M8.5 4.5 12 8l-3.5 3.5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
          </motion.p>

          {stats && (
            <motion.p
              className="fx-hero-facts"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.8, duration: 0.5 }}
            >
              <span>{stats.offers.toLocaleString(tag)} {t("hero.offersTracked")}</span>
              <span aria-hidden="true">·</span>
              <span>{stats.multiMerchant.toLocaleString(tag)} {t("hero.multiMerchant")}</span>
              <span aria-hidden="true">·</span>
              <span>{stats.snapshots.toLocaleString(tag)} {t("hero.snapshots")}</span>
            </motion.p>
          )}
        </div>

        {product && (
          <motion.aside
            className="fx-hero-panel"
            aria-label="Exemple de produit suivi"
            style={{
              rotateX,
              rotateY,
              transformPerspective: 1200,
            }}
            initial={{ opacity: 0, scale: 0.85, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          >
            <article className="fx-card fx-verdict-card">
              <header className="fx-verdict-head">
                <span className="fx-badge brand">{t("hero.tracked")}</span>
                <span className="fx-fine">{product.merchants} {t("hero.sellIt")}</span>
              </header>

              <div className="fx-verdict-product">
                {product.image && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image} alt="" loading="lazy" width={72} height={72} />
                )}
                <div>
                  {product.brand && <span className="fx-eyebrow">{product.brand}</span>}
                  <a className="fx-verdict-name" href={`/produits/${product.ean}/`}>
                    {product.name}
                  </a>
                </div>
              </div>

              <dl className="fx-verdict-rows">
                <div>
                  <dt>{t("hero.highest")}</dt>
                  <dd className="strike">{money(product.priceMax, product.currency)}</dd>
                </div>
                <div>
                  <dt>{t("hero.lowest")}</dt>
                  <dd className="lead">{money(product.priceMin, product.currency)}</dd>
                </div>
              </dl>

              <footer className="fx-verdict-foot">
                <span className="fx-badge gain">
                  −{money(product.priceMax - product.priceMin, product.currency)} {t("hero.gap")}
                </span>
                <a className="fx-verdict-link" href={`/produits/${product.ean}/`}>
                  {t("hero.dossier")}
                  <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                    <path
                      d="M3 8h9M8.5 4.5 12 8l-3.5 3.5"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </a>
              </footer>
            </article>

            <p className="fx-hero-panel-note">
              {t("hero.realData")}
            </p>
          </motion.aside>
        )}
      </div>
    </section>
  );
}
