import type { RecommendationTrace } from "./filon-intelligence";

export type DecisionLedger = {
  constraints: string[];
  catalogue: { considered: number; eligible: number; unavailable: number; unsafe: number };
  policy: string[];
};

/**
 * Trace de décision d’interface : elle décrit les critères, pas une vérité
 * cachée. Aucune commission, préférence partenaire ou donnée non observée n’y
 * est admise.
 */
export function buildDecisionLedger(trace: RecommendationTrace, solutionConstraints: string[]): DecisionLedger {
  const constraints = [...solutionConstraints];
  if (trace.intent.request.trim()) constraints.unshift(`Intention : ${trace.intent.request.trim().slice(0, 160)}`);
  return {
    constraints,
    catalogue: { considered: trace.considered, eligible: trace.eligible, unavailable: trace.excludedUnavailable, unsafe: trace.excludedUnsafe },
    policy: ["Les offres sont filtrées selon leur disponibilité et la validité de leur lien partenaire.", "Les décisions n’utilisent ni commission, ni priorité commerciale, ni prix inventé."],
  };
}
