"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { JsonLd, breadcrumbSchema } from "@/lib/seo";
import { Reveal } from "./Reveal";
import { LifeVideo } from "./LifeVideo";
import { useLocale } from "@/lib/i18n";

export function ContentHero({
  eyebrow,
  title,
  intro,
  breadcrumb,
  photo,
  video,
}: {
  eyebrow: string;
  title: ReactNode;
  intro: ReactNode;
  breadcrumb: { name: string; path: string }[];
  photo?: string;
  video?: string;
}) {
  return (
    <section className="ed-content-hero">
      <JsonLd data={breadcrumbSchema([{ name: "Accueil", path: "/" }, ...breadcrumb])} />
      <div className="ed-wrap">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <span className="eyebrow">{eyebrow}</span>
          <h1 style={{ marginTop: 18 }}>{title}</h1>
          <p className="intro">{intro}</p>
        </motion.div>
        {video && photo ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <LifeVideo src={video} poster={photo} />
          </motion.div>
        ) : photo ? (
          <motion.div
            className="ed-content-photo"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <img src={photo} alt="" loading="lazy" />
          </motion.div>
        ) : null}
      </div>
    </section>
  );
}

/** Editorial two-column block: a serif heading + prose — avec animation au scroll. */
export function ProseBlock({ heading, children, alt = false }: { heading: ReactNode; children: ReactNode; alt?: boolean }) {
  return (
    <section className={`ed-band ${alt ? "alt" : ""}`}>
      <div className="ed-wrap">
        <div className="ed-mgrid">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="ed-prose">
              <h2>{heading}</h2>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ delay: 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="ed-prose">{children}</div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export function InfoGrid({ items }: { items: { n: ReactNode; h: string; p: string }[] }) {
  return (
    <motion.div
      className="ed-infogrid"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-40px" }}
      variants={{
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.12 } },
      }}
    >
      {items.map((it) => (
        <motion.div
          className="ed-info"
          key={it.h}
          variants={{
            hidden: { opacity: 0, y: 30 },
            show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
          }}
        >
          <div className="n mono">{it.n}</div>
          <h3>{it.h}</h3>
          <p>{it.p}</p>
        </motion.div>
      ))}
    </motion.div>
  );
}

export function ClosingCta({ title, sub }: { title: ReactNode; sub?: string }) {
  const { t } = useLocale();
  return (
    <section className="ed-closing" id="installer">
      <div className="ed-wrap">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          style={{ textAlign: "center" }}
        >
          <span className="eyebrow" style={{ display: "block", marginBottom: 26 }}>
            {t("final.eyebrow")}
          </span>
          <h2>{title}</h2>
          {sub ? <p style={{ color: "var(--ink-2)", fontSize: 18, margin: "18px auto 0", maxWidth: "42ch" }}>{sub}</p> : null}
          <motion.a
            className="ed-btn dark"
            href="/recherche"
            style={{ marginTop: "clamp(30px,5vw,44px)" }}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.97 }}
          >
            {t("cta.try")}
          </motion.a>
        </motion.div>
      </div>
    </section>
  );
}
