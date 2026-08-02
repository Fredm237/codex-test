"use client";

import { motion } from "framer-motion";

export type VerdictData = {
  level: string;
  headline: string;
  reasons: string[];
  tracked_days: number;
  samples: number;
  confidence: string;
};

const CONFIDENCE_LABEL: Record<string, string> = {
  faible: "confiance faible",
  moyenne: "confiance moyenne",
  bonne: "bonne confiance",
};

/** Le verdict FILON : la conclusion, avant le détail des offres.
 *
 *  L'ampleur du suivi est affichée avec le verdict, pas cachée : une conclusion
 *  tirée de trois jours de relevés ne vaut pas celle tirée de six mois, et
 *  l'utilisateur doit pouvoir en juger.
 */
export function Verdict({ v }: { v: VerdictData }) {
  if (!v) return null;
  const level = ["excellent", "bon", "neutre", "attendre", "insuffisant"].includes(v.level)
    ? v.level
    : "neutre";

  return (
    <motion.section
      className={`vd vd-${level}`}
      aria-label="Verdict FILON"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <span className="vd-eyebrow">Verdict FILON</span>
      <div className="vd-head">
        <motion.span
          className="vd-dot"
          aria-hidden="true"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: "spring", stiffness: 400, damping: 15 }}
        />
        <b className="vd-title">{v.headline}</b>
      </div>
      {v.reasons?.length > 0 && (
        <motion.ul
          className="vd-reasons"
          initial="hidden"
          animate="show"
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.2 } },
          }}
        >
          {v.reasons.map((r, i) => (
            <motion.li
              key={i}
              variants={{
                hidden: { opacity: 0, x: -8 },
                show: { opacity: 1, x: 0 },
              }}
            >
              {r}
            </motion.li>
          ))}
        </motion.ul>
      )}
      {v.samples > 0 && (
        <p className="vd-meta">
          {v.samples} relevé{v.samples > 1 ? "s" : ""} sur {v.tracked_days} jour
          {v.tracked_days > 1 ? "s" : ""} · {CONFIDENCE_LABEL[v.confidence] ?? v.confidence}
        </p>
      )}
    </motion.section>
  );
}
