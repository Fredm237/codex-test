import { describe, expect, it } from "vitest";

import { fashionExpertContract, makeEvidence, makeRelation } from "../lib/filon-intelligence-contract";

describe("Contrats FILON Intelligence", () => {
  it("ne transforme jamais une inférence ou une absence de preuve en fait vérifié", () => {
    expect(makeEvidence({ value: "navy", source: "filon_inference", confidence: "medium", rationale: "Nom d’offre" }).status).toBe("inferred");
    expect(makeEvidence({ value: "navy", source: "unavailable", confidence: "high", rationale: "Absence de preuve" })).toMatchObject({ value: null, status: "unknown", source: "unavailable" });
    expect(makeEvidence({ value: null, source: "catalogue_partner", confidence: "high", rationale: "Information absente" })).toMatchObject({ value: null, status: "unknown", confidence: "low", source: "unavailable" });
  });

  it("borne les scores de relations et formalise le contrat Fashion extensible", () => {
    const relation = makeRelation({ type: "COMPLEMENTS", subjectId: "offer:1", objectId: "offer:2", score: 3, justification: "Rôles complémentaires", evidence: makeEvidence({ value: true, source: "filon_inference", confidence: "medium", rationale: "Rôle de tenue" }), updatedAt: "2026-08-16T00:00:00.000Z" });
    expect(relation.score).toBe(1);
    expect(fashionExpertContract.relationTypes).toContain("INCOMPATIBLE_WITH");
  });
});
