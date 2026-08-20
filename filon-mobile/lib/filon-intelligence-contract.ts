export type EvidenceConfidence = "high" | "medium" | "low";
export type EvidenceStatus = "verified" | "inferred" | "unknown";
export type EvidenceSource = "merchant" | "product_description" | "catalogue_partner" | "filon_inference" | "user_declared" | "unavailable";

export type IntelligenceEvidence<T> = {
  value: T | null;
  status: EvidenceStatus;
  confidence: EvidenceConfidence;
  source: EvidenceSource;
  rationale: string;
  observedAt: string | null;
};

export type IntelligenceRelationType = "COMPATIBLE_WITH" | "COMPLEMENTS" | "ALTERNATIVE_TO" | "SIMILAR_TO" | "CONTRASTS_WITH" | "BELONGS_TO_STYLE" | "SUITABLE_FOR" | "SUITABLE_IN_SEASON" | "SUITABLE_FOR_CONTEXT" | "RECOMMENDED_WITH" | "INCOMPATIBLE_WITH";

export type IntelligenceRelation = {
  type: IntelligenceRelationType;
  subjectId: string;
  objectId: string | null;
  score: number;
  justification: string;
  evidence: IntelligenceEvidence<true>;
  updatedAt: string;
};

export type DomainExpertContract = {
  domainId: string;
  taxonomyVersion: string;
  relationTypes: IntelligenceRelationType[];
  scoreDimensions: string[];
  supportsBenchmark: boolean;
  supportsFeedback: boolean;
};

/** Une inférence ne peut jamais être promue en fait confirmé par ce contrat. */
export function makeEvidence<T>(input: { value: T | null; source: EvidenceSource; confidence: EvidenceConfidence; rationale: string; observedAt?: string | null }): IntelligenceEvidence<T> {
  const status: EvidenceStatus = input.value === null || input.source === "unavailable" ? "unknown" : input.source === "filon_inference" ? "inferred" : "verified";
  return { value: status === "unknown" ? null : input.value, status, confidence: status === "unknown" ? "low" : input.confidence, source: status === "unknown" ? "unavailable" : input.source, rationale: input.rationale.trim().slice(0, 240), observedAt: input.observedAt ?? null };
}

export function makeRelation(input: Omit<IntelligenceRelation, "score" | "evidence" | "updatedAt"> & { score: number; evidence: IntelligenceEvidence<true>; updatedAt?: string }): IntelligenceRelation {
  return { ...input, score: Math.max(0, Math.min(1, input.score)), evidence: makeEvidence(input.evidence), updatedAt: input.updatedAt ?? new Date().toISOString() };
}

export const fashionExpertContract: DomainExpertContract = {
  domainId: "fashion",
  taxonomyVersion: "v1",
  relationTypes: ["COMPATIBLE_WITH", "COMPLEMENTS", "ALTERNATIVE_TO", "SIMILAR_TO", "CONTRASTS_WITH", "BELONGS_TO_STYLE", "SUITABLE_FOR", "SUITABLE_IN_SEASON", "SUITABLE_FOR_CONTEXT", "RECOMMENDED_WITH", "INCOMPATIBLE_WITH"],
  scoreDimensions: ["style", "context", "availability", "budget", "confidence"],
  supportsBenchmark: true,
  supportsFeedback: true,
};
