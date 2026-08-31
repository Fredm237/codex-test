import { describe, expect, it } from "vitest";

import { buildDecisionLedger } from "../lib/filon-decision-ledger";
import { resolveOutfitPublicMessage } from "../lib/filon-outfit-i18n";

describe("Registre de décision FILON", () => {
  it("restitue les compteurs observés et les contraintes sans introduire de signal commercial", () => {
    const ledger = buildDecisionLedger({ intent: { request: "tenue travail", occasion: "work", season: "spring", budget: 200, declaredStyle: null }, considered: 14, eligible: 7, excludedNonEligible: 4, excludedUnsafe: 3 }, [{ code: "constraint.budget_respected", amount: 200, currency: "EUR" }]);
    expect(ledger.catalogue).toEqual({ considered: 14, eligible: 7, nonEligible: 4, unsafe: 3 });
    expect(ledger.catalogue.eligible + ledger.catalogue.nonEligible + ledger.catalogue.unsafe).toBe(ledger.catalogue.considered);
    expect(ledger.constraints[0]).toEqual({ code: "ledger.intent", value: "tenue travail" });
    expect(ledger.constraints[1]).toEqual({ code: "constraint.budget_respected", amount: 200, currency: "EUR" });
    expect(ledger.policy).toEqual([{ code: "ledger.policy.offer_classification" }, { code: "ledger.policy.no_commercial_priority" }]);
    expect(resolveOutfitPublicMessage(ledger.constraints[0], "en")).toContain("tenue travail");
    expect(resolveOutfitPublicMessage(ledger.policy[1], "fr")).toContain("ni commission");
  });
});
