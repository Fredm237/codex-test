"use client";

import { useEffect, useState } from "react";
import { Reveal } from "./Reveal";

/**
 * Vidéo « vivante » réutilisable : autoplay muette en boucle, poster affiché
 * pendant le chargement, repli sur l'image fixe si l'utilisateur a demandé à
 * réduire les animations. Aucun son, aucun contrôle : c'est un visuel.
 */
export function LifeVideo({ src, poster, className = "ed-content-photo" }: { src: string; poster: string; className?: string }) {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  return (
    <Reveal className={className}>
      {reduced ? (
        <img src={poster} alt="" loading="lazy" />
      ) : (
        <video autoPlay muted loop playsInline poster={poster} aria-hidden="true">
          <source src={src} type="video/mp4" />
        </video>
      )}
    </Reveal>
  );
}
