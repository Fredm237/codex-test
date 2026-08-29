// Version alignée sur filon-currency-roster-2026-08-29-v1 côté API.
// Une nouvelle devise doit être ajoutée explicitement aux deux frontières :
// trois lettres seules ne constituent pas une preuve de comparabilité.
export const SUPPORTED_CURRENCY_CODES = new Set([
  "EUR", "CHF", "GBP", "DKK", "SEK", "NOK", "ISK", "PLN", "CZK", "HUF", "RON", "BGN",
  "ALL", "BAM", "MKD", "RSD", "MDL", "UAH", "TRY", "GEL", "AMD", "AZN", "USD", "CAD",
  "AUD", "NZD", "JPY", "CNY", "HKD", "SGD", "KRW", "INR", "AED", "SAR", "ILS", "ZAR",
]);

export function normalizeSupportedCurrency(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const code = value.trim().toUpperCase();
  return SUPPORTED_CURRENCY_CODES.has(code) ? code : null;
}

export type SupportedMoney = {
  amount: number;
  currency: string;
};

/** Un montant n'est affichable que si valeur et devise sont toutes deux prouvées. */
export function normalizeSupportedMoney(amount: unknown, currency: unknown): SupportedMoney | null {
  if (typeof amount !== "number" || !Number.isFinite(amount) || amount <= 0) return null;
  const code = normalizeSupportedCurrency(currency);
  return code === null ? null : { amount, currency: code };
}

/** Formate sans symbole ni devise de secours ; l'inconnue reste `null`. */
export function formatSupportedMoney(
  amount: unknown,
  currency: unknown,
  locale: "fr" | "nl" | "en" = "fr",
): string | null {
  const money = normalizeSupportedMoney(amount, currency);
  if (money === null) return null;
  const numberLocale = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  try {
    return new Intl.NumberFormat(numberLocale, {
      style: "currency",
      currency: money.currency,
      maximumFractionDigits: 2,
    }).format(money.amount);
  } catch {
    return null;
  }
}
