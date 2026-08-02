"use client";

// Respect du réglage « réduire les animations » du système, pour toute
// l'application d'un seul endroit.
//
// framer-motion ne le fait pas tout seul : chaque `motion.*` s'anime, que la
// personne l'ait demandé ou non. Les animations ajoutées lors de la refonte —
// transitions de page, ressorts au survol, cascades au scroll — l'ignoraient
// donc toutes. Ce n'est pas un détail de confort : pour une personne sujette
// au mal des transports ou aux troubles vestibulaires, une interface qui
// bouge sans arrêt est inutilisable, et c'est un critère WCAG 2.2.
//
// `reducedMotion="user"` supprime les animations de transformation quand le
// système le demande, et conserve les fondus d'opacité — qui ne déclenchent
// pas ces troubles. Une ligne, appliquée partout, plutôt qu'un `useReducedMotion`
// oublié dans un composant sur deux.

import { MotionConfig } from "framer-motion";
import type { ReactNode } from "react";

export function MotionProvider({ children }: { children: ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
