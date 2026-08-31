import { normalizeFilonObservedAt, type FilonCataloguePulse } from "./filon-api";
import type { FilonLocale } from "@/lib/locale";

const copy = {
  fr: { checking: "Contrôle de la source", syncing: "Synchronisation source en cours", inactive: "Source momentanément inactive", lastReading: "Dernier relevé" },
  nl: { checking: "Bronstatus ophalen", syncing: "Bronsynchronisatie bezig", inactive: "Bron tijdelijk niet actief", lastReading: "Laatste meting" },
  en: { checking: "Reading source status", syncing: "Source sync in progress", inactive: "Source temporarily inactive", lastReading: "Last reading" },
};

export function catalogueSourceState(pulse: FilonCataloguePulse | undefined, locale: FilonLocale, now: number | Date = Date.now()) {
  const text = copy[locale];
  if (!pulse) return { label: text.checking, tone: "pending" as const };
  if (pulse.syncStatus === "syncing") return { label: text.syncing, tone: "pending" as const };
  if (!pulse.live) return { label: text.inactive, tone: "muted" as const };
  if (!pulse.lastReading) return { label: text.checking, tone: "pending" as const };
  const observedAt = normalizeFilonObservedAt(pulse.lastReading);
  const reference = now instanceof Date ? now.getTime() : now;
  if (observedAt === null || !Number.isFinite(reference)) return { label: text.checking, tone: "pending" as const };
  const date = new Date(observedAt);
  const age = reference - date.getTime();
  if (age < 0) return { label: text.checking, tone: "pending" as const };
  if (age > 24 * 60 * 60 * 1000) return { label: text.inactive, tone: "muted" as const };
  return { label: `${text.lastReading} · ${new Intl.DateTimeFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { day: "2-digit", month: "short" }).format(date)}`, tone: "live" as const };
}
