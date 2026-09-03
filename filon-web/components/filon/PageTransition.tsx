"use client";

import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  PRODUCT_JOURNEY_EVENT,
  type ProductJourneyDetail,
} from "@/components/experience/ProductJourneyLink";

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
  const previousPath = useRef(pathname);
  type Handoff = ProductJourneyDetail & {
    destination: ProductJourneyDetail["source"];
    settled: boolean;
  };
  const handoffRef = useRef<Handoff | null>(null);
  const [handoff, setHandoff] = useState<Handoff | null>(null);

  useEffect(() => {
    const begin = (event: Event) => {
      const detail = (event as CustomEvent<ProductJourneyDetail>).detail;
      const width = Math.min(280, Math.max(96, detail.source.width));
      const ratio = detail.source.height / Math.max(detail.source.width, 1);
      const height = width * Math.max(0.7, Math.min(1.35, ratio));
      const next = {
        ...detail,
        destination: {
          height,
          left: window.innerWidth / 2 - width / 2,
          top: window.innerHeight / 2 - height / 2,
          width,
        },
        settled: false,
      };
      handoffRef.current = next;
      setHandoff(next);
    };
    window.addEventListener(PRODUCT_JOURNEY_EVENT, begin);
    return () => window.removeEventListener(PRODUCT_JOURNEY_EVENT, begin);
  }, []);

  useEffect(() => {
    if (previousPath.current === pathname) return;
    previousPath.current = pathname;
    if (!handoffRef.current) return;
    let clearTimer = 0;
    const frame = requestAnimationFrame(() => {
      const target = document.querySelector("[data-product-transition-target] img");
      const rect = target?.getBoundingClientRect();
      setHandoff((current) => current ? {
        ...current,
        destination: rect && rect.width > 0 && rect.height > 0
          ? { height: rect.height, left: rect.left, top: rect.top, width: rect.width }
          : current.destination,
        settled: true,
      } : null);
      clearTimer = window.setTimeout(() => {
        handoffRef.current = null;
        setHandoff(null);
      }, 720);
    });
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(clearTimer);
    };
  }, [pathname]);

  return (
    <div className="fx-continuity" data-experience-chapter={chapter}>
      <AnimatePresence>
        {handoff ? (
          <motion.div
            key={`${handoff.image}-${handoff.label}`}
            className="fx-product-handoff"
            aria-hidden="true"
            initial={{
              height: handoff.source.height,
              left: handoff.source.left,
              opacity: 1,
              top: handoff.source.top,
              width: handoff.source.width,
            }}
            animate={{
              height: handoff.destination.height,
              left: handoff.destination.left,
              opacity: handoff.settled ? 0 : 1,
              top: handoff.destination.top,
              width: handoff.destination.width,
            }}
            exit={{ opacity: 0 }}
            transition={{ duration: handoff.settled ? 0.58 : 0.46, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={handoff.image} alt="" />
            <span>{handoff.label}</span>
          </motion.div>
        ) : null}
      </AnimatePresence>

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
