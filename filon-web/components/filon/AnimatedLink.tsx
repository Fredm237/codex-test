"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * Lien avec micro-interaction au survol.
 * 
 * Effet : un léger soulignement animé apparaît de gauche à droite,
 * donnant une sensation de réactivité et de vie à chaque lien.
 */
export function AnimatedLink({
  children,
  className = "",
  href,
  target,
  rel,
}: {
  children: ReactNode;
  className?: string;
  href?: string;
  target?: string;
  rel?: string;
}) {
  return (
    <motion.a
      className={`fx-animated-link ${className}`}
      href={href}
      target={target}
      rel={rel}
      whileHover={{ x: 2 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {children}
    </motion.a>
  );
}
