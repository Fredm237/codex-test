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
import { observationTimestamp } from "./product-copy";

export type PulseData = {
  live: boolean;
  lastReading: string | null;
  readings24h: number;
  drops24h: number;
  dropsComparable?: boolean;
};

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;
const FRESH_MS = 6 * 60 * 60 * 1000;
const ROLLING_WINDOW_MS = 24 * 60 * 60 * 1000;
const POLL_MS = 2 * 60 * 1000;
const METRICS_MAX_AGE_MS = 3 * 60 * 1000;
const BASE_PATH = (process.env.NEXT_PUBLIC_BASE_PATH || "").replace(/\/$/, "");
const PULSE_PROXY_PATH = `${BASE_PATH}/api/catalog/pulse`;

function parsePulse(value: unknown): PulseData | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  const raw = value as Record<string, unknown>;
  if (raw.live !== true) return null;
  const count = (entry: unknown) => (
    typeof entry === "number" && Number.isSafeInteger(entry) && entry >= 0 ? entry : 0
  );
  return {
    live: true,
    lastReading: typeof raw.last_reading === "string" ? raw.last_reading : null,
    readings24h: count(raw.readings_24h),
    drops24h: count(raw.drops_24h),
    dropsComparable: raw.drops_comparable === true,
  };
}

/** « il y a 3 min », « il y a 2 h », « hier ». */
function ago(timestamp: number, now: number, t: (k: string) => string): string {
  const minutes = Math.round((now - timestamp) / 60000);
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
  // Zéro garde aussi le rendu serveur fail-closed et évite de figer l'heure
  // de construction dans le HTML hydraté.
  const [now, setNow] = useState(0);
  const [snapshot, setSnapshot] = useState<PulseData | null>(data);
  // Les compteurs portent une fenêtre roulante. Ils ne sont rendus qu'après
  // une lecture navigateur réussie, puis expirent si le polling est interrompu.
  const [metricsCheckedAt, setMetricsCheckedAt] = useState(0);
  useEffect(() => {
    const update = () => setNow(Date.now());
    update();
    let active = true;
    let controller: AbortController | null = null;
    const refresh = async () => {
      if (document.visibilityState === "hidden") return;
      controller?.abort();
      const requestController = new AbortController();
      controller = requestController;
      const timeout = window.setTimeout(() => requestController.abort(), 8000);
      try {
        const response = await fetch(PULSE_PROXY_PATH, {
          headers: { accept: "application/json" },
          signal: requestController.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload: unknown = await response.json();
        const next = parsePulse(payload);
        const raw = typeof payload === "object" && payload !== null && !Array.isArray(payload)
          ? payload as Record<string, unknown>
          : null;
        const checkedAt = typeof raw?.proxy_checked_at === "string"
          ? observationTimestamp(raw.proxy_checked_at)
          : null;
        const receivedAt = Date.now();
        if (!active) return;
        setNow(receivedAt);
        setSnapshot(next);
        // La date de contrôle vient de la lecture Railway mise en cache. Une
        // réponse partagée ne peut donc pas rajeunir indéfiniment les
        // agrégats si la source tombe. Métadonnée absente/future : inconnu.
        setMetricsCheckedAt(
          next && checkedAt !== null && checkedAt <= receivedAt ? checkedAt : 0,
        );
      } catch {
        // Le dernier horodatage reste affichable et vieillit naturellement,
        // mais les agrégats roulants cessent d'être affirmés.
        if (active) setMetricsCheckedAt(0);
      } finally {
        window.clearTimeout(timeout);
        if (controller === requestController) controller = null;
      }
    };
    void refresh();
    const clockId = window.setInterval(update, 60000);
    const pollId = window.setInterval(() => { void refresh(); }, POLL_MS);
    const onVisible = () => {
      if (document.visibilityState !== "visible") return;
      update();
      void refresh();
    };
    const onPageShow = () => { update(); void refresh(); };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("pageshow", onPageShow);
    return () => {
      active = false;
      controller?.abort();
      window.clearInterval(clockId);
      window.clearInterval(pollId);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("pageshow", onPageShow);
    };
  }, []);

  if (!snapshot?.live || !snapshot.lastReading) return null;
  const timestamp = observationTimestamp(snapshot.lastReading);
  if (timestamp === null) return null;
  const age = now - timestamp;
  // Une date future ne prouve aucune activité actuelle. Elle est masquée au
  // lieu d'être arrondie artificiellement à « maintenant ».
  if (age < 0) return null;

  const fresh = age <= FRESH_MS;
  const rollingMetricsCurrent = age <= ROLLING_WINDOW_MS
    && metricsCheckedAt > 0
    && now >= metricsCheckedAt
    && now - metricsCheckedAt <= METRICS_MAX_AGE_MS;
  const n = (v: number) => v.toLocaleString(TAG[locale]);

  return (
    <p className="fx-pulse" aria-live="off">
      <span className={`fx-pulse-dot${fresh ? " on" : ""}`} aria-hidden="true" />
      <span>
        {t("pulse.last")} {ago(timestamp, now, t)}
      </span>
      {rollingMetricsCurrent && snapshot.readings24h > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span>
            <b>{n(snapshot.readings24h)}</b> {t("pulse.readings")}
          </span>
        </>
      )}
      {rollingMetricsCurrent && snapshot.dropsComparable === true && snapshot.drops24h > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span className="fx-pulse-drop">
            <b>{n(snapshot.drops24h)}</b> {t("pulse.drops")}
          </span>
        </>
      )}
    </p>
  );
}
