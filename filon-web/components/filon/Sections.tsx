"use client";

// Sections de la home — Refonte TOTALE août 2026.
// Chaque étape a maintenant une illustration 3D premium.
// Le Closing utilise un fond dramatique avec particules dorées.

import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";

const STEP_IMAGES = [
  "/img/method-step1.png",
  "/img/method-step2.png",
  "/img/method-step3.png",
];

const STEP_KEYS = ["1", "2", "3"];

export function Method() {
  const { t } = useLocale();
  return (
    <section className="fx-section fx-method" id="methode">
      <div className="fx-container">
        <motion.div
          className="fx-method-header"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
        >
          <h2 className="fx-method-title">
            {t("method.t1")}
            <br />
            <em>{t("method.t2")}</em>
          </h2>
        </motion.div>

        <motion.ol
          className="fx-method-steps"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-40px" }}
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.2, delayChildren: 0.1 } },
          }}
        >
          {STEP_KEYS.map((n, i) => (
            <motion.li
              className="fx-method-step"
              key={n}
              variants={{
                hidden: { opacity: 0, y: 60 },
                show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } },
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="fx-method-step-img"
                src={STEP_IMAGES[i]}
                alt=""
                loading="lazy"
                width={240}
                height={240}
              />
              <div className="fx-method-step-content">
                <span className="fx-method-step-n">0{n}</span>
                <h3 className="fx-method-step-title">{t(`method.s${n}t`)}</h3>
                <p className="fx-method-step-body">{t(`method.s${n}b`)}</p>
              </div>
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  );
}

export function Closing({ proof }: { proof: Proof | null }) {
  const { t, locale } = useLocale();
  const tag = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const stats = proof?.stats ?? null;
  return (
    <section className="fx-closing">
      <video
        className="fx-closing-bg-video"
        autoPlay
        muted
        loop
        playsInline
        aria-hidden="true"
      >
        <source src="/video/closing_bg.mp4" type="video/mp4" />
      </video>
      <div className="fx-closing-overlay" aria-hidden="true" />
      <motion.div
        className="fx-container narrow fx-closing-content"
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
      >
        <h2 className="fx-closing-title">
          {t("closing.t1")}
          <br />
          <em>{t("closing.t2")}</em>
        </h2>
        <p className="fx-closing-lede">
          {stats
            ? `${stats.offers.toLocaleString(tag)} ${t("closing.factsA")} ${stats.merchants.toLocaleString(tag)} ${t("closing.factsB")}`
            : t("closing.fallback")}
        </p>
        <motion.div
          className="fx-closing-actions"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, duration: 0.5, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
        >
          <a className="fx-btn fx-btn-light" href="/recherche/">
            {t("cta.try")}
          </a>
          <a className="fx-btn fx-btn-ghost-light" href="/catalogue/">
            {t("hero.explore")}
          </a>
        </motion.div>
      </motion.div>
    </section>
  );
}
