import type { FilonCataloguePulse } from "@/lib/filon-api";
import type { FilonLocale } from "@/lib/locale";

const copy = {
  fr: { checking: "Vérification de la source", syncing: "Synchronisation source en cours", inactive: "Source momentanément inactive", lastReading: "Dernier relevé" },
  nl: { checking: "Bron wordt gecontroleerd", syncing: "Bronsynchronisatie bezig", inactive: "Bron tijdelijk niet actief", lastReading: "Laatste meting" },
  en: { checking: "Checking source", syncing: "Source sync in progress", inactive: "Source temporarily inactive", lastReading: "Last reading" },
};

export function catalogueSourceState(pulse: FilonCataloguePulse | undefined, locale: FilonLocale) {
  const text = copy[locale];
  if (!pulse) return { label: text.checking, tone: "pending" as const };
  if (pulse.syncStatus === "syncing") return { label: text.syncing, tone: "pending" as const };
  if (!pulse.live) return { label: text.inactive, tone: "muted" as const };
  if (!pulse.lastReading) return { label: text.checking, tone: "pending" as const };
  const date = new Date(pulse.lastReading);
  if (Number.isNaN(date.getTime())) return { label: text.checking, tone: "pending" as const };
  return { label: `${text.lastReading} · ${new Intl.DateTimeFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { day: "2-digit", month: "short" }).format(date)}`, tone: "live" as const };
}
