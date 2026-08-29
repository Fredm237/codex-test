"use client";

import { useEffect, useState } from "react";
import { OFFER_MAX_AGE_HOURS, observationTimestamp } from "./product-copy";

const MAX_TIMER_DELAY = 2_147_000_000;
const HOUR_MS = 60 * 60 * 1000;
const MAX_AGE_MS = OFFER_MAX_AGE_HOURS * 60 * 60 * 1000;

/**
 * Horloge fail-closed des surfaces d'offre. Le rendu serveur et la première
 * hydratation utilisent zéro, donc aucun CTA n'est ouvert avant le contrôle
 * client. Un timer réveille ensuite le composant exactement à l'expiration du
 * prochain relevé, y compris après un retour depuis le cache du navigateur.
 */
export function useEvidenceNow(values: readonly unknown[]): number {
  const [now, setNow] = useState(0);
  const timestamps = values
    .map(observationTimestamp)
    .filter((value): value is number => value !== null)
    .sort((left, right) => left - right);
  const signature = timestamps.join(",");

  useEffect(() => {
    let timer: number | null = null;
    const schedule = () => {
      if (timer !== null) window.clearTimeout(timer);
      const reference = Date.now();
      setNow(reference);
      // DecisionPanel affiche un âge entier en heures : son horloge doit donc
      // avancer à chaque frontière horaire, pas seulement à 24/48/72 h.
      // Une date légèrement future (décalage d'horloge du flux) provoque aussi
      // un nouveau contrôle à son instant, sans être admise avant celui-ci.
      const nextExpiry = timestamps
        .flatMap((timestamp) => {
          if (timestamp > reference) return [timestamp];
          const expiry = timestamp + MAX_AGE_MS;
          if (reference > expiry) return [];
          const completedHours = Math.floor((reference - timestamp) / HOUR_MS);
          const nextHour = timestamp + (completedHours + 1) * HOUR_MS;
          // À 72 h exactes la preuve est encore admise. Le délai de 25 ms
          // ci-dessous relance juste après cette frontière et ferme l'action.
          return [Math.min(nextHour, expiry)];
        })
        .filter((timestamp) => timestamp >= reference)
        .sort((left, right) => left - right)[0];
      timer = nextExpiry === undefined
        ? null
        : window.setTimeout(schedule, Math.min(MAX_TIMER_DELAY, Math.max(0, nextExpiry - reference + 25)));
    };
    schedule();
    const onVisibility = () => { if (document.visibilityState === "visible") schedule(); };
    window.addEventListener("pageshow", schedule);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      if (timer !== null) window.clearTimeout(timer);
      window.removeEventListener("pageshow", schedule);
      document.removeEventListener("visibilitychange", onVisibility);
    };
    // `signature` est la représentation stable des dates; le tableau brut est
    // volontairement exclu car les pages produit le recréent à chaque rendu.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  return now;
}
