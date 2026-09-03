"use client";

import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type JourneyChapter = "signal" | "market" | "identity" | "proof" | "decision" | "compose";

const CHAPTER_PATHS: ReadonlyArray<[JourneyChapter, RegExp]> = [
  ["compose", /^\/creer(?:\/|$)/],
  ["identity", /^\/produits?(?:\/|$)/],
  ["market", /^\/(?:recherche|catalogue|categorie|marchands)(?:\/|$)/],
  ["decision", /^\/(?:score|cashback|codes-promo|reconditionne)(?:\/|$)/],
  ["proof", /^\/(?:intelligence|comment-ca-marche|transparence|securite)(?:\/|$)/],
];

export function resolveJourneyChapter(pathname: string): JourneyChapter {
  return CHAPTER_PATHS.find(([, pattern]) => pattern.test(pathname))?.[0] ?? "signal";
}

/**
 * Le site n'est pas une collection de pages : chaque navigation recadre la
 * même table de décision. Le contenu reste du DOM immédiatement utilisable ;
 * le mouvement ne porte ni information ni contrôle.
 */
export function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const chapter = resolveJourneyChapter(pathname);

  return (
    <div className="fx-continuity" data-experience-chapter={chapter}>
      <AnimatePresence initial={false}>
        <motion.div
          key={`field-${pathname}`}
          aria-hidden="true"
          className="fx-continuity-sweep"
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12, delay: 0.72 }}
        >
          <motion.span
            initial={{ x: "-46vw", skewX: -8 }}
            animate={{ x: "146vw", skewX: -8 }}
            transition={{ duration: 0.72, ease: [0.76, 0, 0.24, 1] }}
          >
            <i />
          </motion.span>
        </motion.div>
      </AnimatePresence>

      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={pathname}
          className="fx-continuity-page"
          initial={{ opacity: 0, y: 18, scale: 0.994, rotateX: 1.2 }}
          animate={{ opacity: 1, y: 0, scale: 1, rotateX: 0 }}
          exit={{ opacity: 0, y: -10, scale: 0.997, rotateX: -0.6 }}
          transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
