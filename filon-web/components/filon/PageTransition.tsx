"use client";

import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Transition entre pages — un fondu subtil avec un léger glissement vertical.
 * 
 * Pourquoi :
 * - Élimine la coupure abrupte entre les pages (sensation "app native")
 * - Le mouvement vertical guide le regard vers le contenu frais
 * - La durée courte (300ms) évite de ralentir la navigation
 * - L'easing [0.16, 1, 0.3, 1] est la courbe signature de Filon
 */
export function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{
          duration: 0.3,
          ease: [0.16, 1, 0.3, 1],
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
