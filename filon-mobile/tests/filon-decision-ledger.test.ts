import { describe, expect, it } from "vitest";

import { buildDecisionLedger } from "../lib/filon-decision-ledger";

describe("Registre de décision FILON", () => {
  it("restitue les compteurs observés et les contraintes sans introduire de signal commercial", () => {
    const ledger = buildDecisionLedger({ intent: { request: "tenue travail", occasion: "Travail", season: "Printemps", budget: 200, declaredStyle: null }, considered: 14, eligible: 7, excludedUnavailable: 4, excludedUnsafe: 3 }, ["Budget respecté"]);
    expect(ledger.catalogue).toEqual({ considered: 14, eligible: 7, unavailable: 4, unsafe: 3 });
    expect(ledger.constraints[0]).toContain("tenue travail");
    expect(ledger.policy.join(" ")).toContain("ni commission");
  });
});
