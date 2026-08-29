import type { RecommendationTrace } from "./filon-intelligence";
import type { OutfitPublicMessage } from "./filon-outfit-i18n";

export type DecisionLedger = {
  constraints: OutfitPublicMessage[];
  catalogue: { considered: number; eligible: number; nonEligible: number; unsafe: number };
  policy: OutfitPublicMessage[];
};

/**
 * Trace de décision d’interface : elle décrit les critères, pas une vérité
 * cachée. Aucune commission, préférence partenaire ou donnée non observée n’y
 * est admise.
 */
export function buildDecisionLedger(trace: RecommendationTrace, solutionConstraints: OutfitPublicMessage[]): DecisionLedger {
  const constraints = [...solutionConstraints];
  if (trace.intent.request.trim()) constraints.unshift({ code: "ledger.intent", value: trace.intent.request.trim().slice(0, 160) });
  return {
    constraints,
    catalogue: { considered: trace.considered, eligible: trace.eligible, nonEligible: trace.excludedNonEligible, unsafe: trace.excludedUnsafe },
    policy: [{ code: "ledger.policy.offer_classification" }, { code: "ledger.policy.no_commercial_priority" }],
  };
}
