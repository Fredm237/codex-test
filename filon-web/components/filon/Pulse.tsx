"use client";

// Le pouls du catalogue.
//
// Un site est mort quand rien n'y indique que quelque chose tourne. Ces trois
// faits — dernier relevé, relevés du jour, baisses du jour — viennent de la
// base et changent tout seuls d'heure en heure. Le point qui bat n'est pas une
// décoration : il ne s'affiche que si un relevé a eu lieu dans les six
// dernières heures. Passé ce délai, on le dit franchement plutôt que de
// simuler une activité qui n'existe pas.
//
// Le « il y a X » se recalcule côté client toutes les minutes : servi depuis
// une page mise en cache, un horodatage figé vieillirait en silence.

import { useEffect, useState } from "react";
import { useLocale } from "@/lib/i18n";

export type PulseData = {
  live: boolean;
  lastReading: string | null;
  readings24h: number;
  drops24h: number;
};

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;
const FRESH_MS = 6 * 60 * 60 * 1000;

/** « il y a 3 min », « il y a 2 h », « hier ». */
function ago(iso: string, t: (k: string) => string): string {
  const minutes = Math.max(0, Math.round((Date.now() - Date.parse(iso)) / 60000));
  if (minutes < 1) return t("pulse.now");
  if (minutes < 60) return `${t("pulse.ago")} ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${t("pulse.ago")} ${hours} h`;
  const days = Math.round(hours / 24);
  return days === 1 ? t("pulse.yesterday") : `${t("pulse.ago")} ${days} ${t("pulse.days")}`;
}

export function Pulse({ data }: { data: PulseData | null }) {
  const { t, locale } = useLocale();
  // Réveil toutes les minutes : le « il y a X » doit vieillir sous les yeux.
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 60000);
    return () => clearInterval(id);
  }, []);

  if (!data?.live || !data.lastReading) return null;

  const fresh = Date.now() - Date.parse(data.lastReading) < FRESH_MS;
  const n = (v: number) => v.toLocaleString(TAG[locale]);

  return (
    <p className="fx-pulse" aria-live="off">
      <span className={`fx-pulse-dot${fresh ? " on" : ""}`} aria-hidden="true" />
      <span>
        {t("pulse.last")} {ago(data.lastReading, t)}
      </span>
      {data.readings24h > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span>
            <b>{n(data.readings24h)}</b> {t("pulse.readings")}
          </span>
        </>
      )}
      {data.drops24h > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span className="fx-pulse-drop">
            <b>{n(data.drops24h)}</b> {t("pulse.drops")}
          </span>
        </>
      )}
    </p>
  );
}
