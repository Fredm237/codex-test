import { useEffect, useState } from "react";
import { AppState } from "react-native";

import { FILON_OFFER_MAX_AGE_HOURS, normalizeFilonObservedAt } from "@/lib/filon-api";

const MAX_TIMER_DELAY = 2_147_000_000;

/**
 * Horloge des preuves visibles. Elle réveille l'écran à l'expiration exacte
 * du prochain relevé et au retour au premier plan. Un écran laissé ouvert ne
 * peut donc pas conserver un stock, une baisse ou un CTA devenu ancien.
 */
export function useFilonEvidenceNow(
  values: readonly unknown[],
  maxAgeHours = FILON_OFFER_MAX_AGE_HOURS,
) {
  const [now, setNow] = useState(() => Date.now());
  const observations = values
    .map(normalizeFilonObservedAt)
    .filter((value): value is string => value !== null)
    .sort();
  const signature = `${maxAgeHours}:${observations.join(",")}`;

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const schedule = () => {
      if (timer !== null) clearTimeout(timer);
      const reference = Date.now();
      setNow(reference);
      const maxAgeMs = Math.max(0, maxAgeHours) * 60 * 60 * 1000;
      const nextExpiry = observations
        .map((value) => Date.parse(value) + maxAgeMs)
        .filter((expiry) => expiry >= reference)
        .sort((left, right) => left - right)[0];
      timer = nextExpiry === undefined
        ? null
        : setTimeout(schedule, Math.min(MAX_TIMER_DELAY, Math.max(0, nextExpiry - reference + 25)));
    };
    schedule();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") schedule();
    });
    return () => {
      if (timer !== null) clearTimeout(timer);
      subscription.remove();
    };
    // `signature` contient la liste normalisée et le seuil. Le tableau brut est
    // recréé par les écrans et ne doit pas relancer l'effet à chaque rendu.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  return now;
}
