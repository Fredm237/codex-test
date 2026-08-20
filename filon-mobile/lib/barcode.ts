export function normalizeProductCode(value: string) {
  const digits = value.replace(/\D/g, "");
  return [8, 12, 13, 14].includes(digits.length) ? digits : null;
}
