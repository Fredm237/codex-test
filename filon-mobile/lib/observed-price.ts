export type ObservedPricePoint = { price: number; at: string | null };
export type ObservedPriceSignal = { kind: "down" | "up" | "stable" | "insufficient"; delta: number | null; comparedAt: string | null };

export function deriveObservedPriceSignal(history: ObservedPricePoint[]): ObservedPriceSignal {
  const points = history.filter((point) => Number.isFinite(point.price) && point.price >= 0 && typeof point.at === "string" && Number.isFinite(Date.parse(point.at))).sort((a, b) => Date.parse(a.at!) - Date.parse(b.at!));
  if (points.length < 2) return { kind: "insufficient", delta: null, comparedAt: null };
  const previous = points.at(-2)!;
  const latest = points.at(-1)!;
  const delta = latest.price - previous.price;
  return { kind: delta < 0 ? "down" : delta > 0 ? "up" : "stable", delta: Math.abs(delta), comparedAt: latest.at };
}
