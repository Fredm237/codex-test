const GTIN_LENGTHS = new Set([8, 12, 13, 14]);

function gtinCheckDigit(payload: string) {
  const sum = [...payload]
    .reverse()
    .reduce((total, digit, index) => total + Number(digit) * (index % 2 === 0 ? 3 : 1), 0);
  return (10 - (sum % 10)) % 10;
}

/**
 * Normalize a scanned retail identifier to the same canonical key as Core.
 *
 * Formatting characters are tolerated, but invalid checksums and placeholder
 * identifiers remain unknown. UPC-A and zero-prefixed GTIN-14 converge on the
 * EAN-13 key used by the catalogue instead of producing false misses.
 */
export function normalizeProductCode(value: string) {
  const digits = value.replace(/\D/g, "");
  if (!GTIN_LENGTHS.has(digits.length) || new Set(digits).size === 1) return null;
  if (gtinCheckDigit(digits.slice(0, -1)) !== Number(digits.at(-1))) return null;
  if (digits.length === 12) return `0${digits}`;
  if (digits.length === 14 && digits.startsWith("0")) return digits.slice(1);
  return digits;
}
