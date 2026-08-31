import type { OutfitStrategy } from "./filon-complete";

export type StrategyComparisonItem = { id: OutfitStrategy["id"]; total: number; currency: string; confidenceScore: null; styleScore: null; pieceCount: number };
export type StrategyComparison = { items: StrategyComparisonItem[]; totalDifference: number | null; confidenceDifference: number | null; coverageDifference: number | null };

/** Compare uniquement les métriques calculées de chaque stratégie ; aucun jugement marchand ou score caché n’est ajouté. */
export function compareOutfitStrategies(strategies: OutfitStrategy[]): StrategyComparison {
  const items = strategies.map((strategy) => ({ id: strategy.id, total: strategy.solution.total, currency: strategy.solution.currency, confidenceScore: strategy.solution.confidenceScore, styleScore: strategy.solution.styleScore, pieceCount: strategy.solution.pieces.length }));
  const safe = items.find((item) => item.id === "safe");
  const signature = items.find((item) => item.id === "signature");
  if (!safe || !signature) return { items, totalDifference: null, confidenceDifference: null, coverageDifference: null };
  return { items, totalDifference: signature.currency === safe.currency ? Math.round((signature.total - safe.total) * 100) / 100 : null, confidenceDifference: null, coverageDifference: signature.pieceCount - safe.pieceCount };
}
