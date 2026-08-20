export type BudgetStatus = "no_budget" | "under" | "near_limit" | "over";
export type BudgetSummary = { budget: number | null; spent: number; remaining: number | null; ratio: number | null; status: BudgetStatus };

/** Aucun prix n’est estimé : le calcul repose exclusivement sur les prix présents dans la proposition. */
export function calculateBudget(spent: number, budget: number | null): BudgetSummary {
  const safeSpent = Number.isFinite(spent) ? Math.max(0, spent) : 0;
  if (budget === null || !Number.isFinite(budget) || budget <= 0) return { budget: null, spent: safeSpent, remaining: null, ratio: null, status: "no_budget" };
  const safeBudget = Math.max(0, budget);
  const remaining = Math.round((safeBudget - safeSpent) * 100) / 100;
  const ratio = Math.round((safeSpent / safeBudget) * 1000) / 1000;
  const status: BudgetStatus = safeSpent > safeBudget ? "over" : ratio >= 0.9 ? "near_limit" : "under";
  return { budget: safeBudget, spent: safeSpent, remaining, ratio, status };
}
