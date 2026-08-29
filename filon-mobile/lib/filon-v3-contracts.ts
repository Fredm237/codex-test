import { currentFilonStock, isFilonObservationFresh, normalizeFilonObservedAt, type FilonOffer } from "./filon-api";

export type V3EvidenceStatus = "verified" | "inferred" | "unknown";
export type V3Confidence = "high" | "medium" | "low";
export type V3Evidence<T> = { value: T | null; status: V3EvidenceStatus; confidence: V3Confidence; source: "catalogue_partner" | "user_declared" | "filon_inference" | "unavailable"; rationale: string; observedAt: string | null };

/** Instantané à sens unique des faits Core : Intelligence ne le modifie jamais. */
export type V3CoreOffer = { offerId: number; name: string; price: V3Evidence<number>; currency: string; availability: V3Evidence<boolean>; merchantName: string; merchantSlug: string | null; imageUrl: string | null; link: string };
export type V3ProductIntelligence = { core: V3CoreOffer; inferredAttributes: Record<string, V3Evidence<string>>; updatedAt: string };
export type V3StyleProfile = { version: string; declaredStyle: string | null; signals: Array<{ source: "declared" | "feedback" | "save"; weight: number; recordedAt: string }> };
export type V3Intent = { request: string; occasion: string | null; season: string | null; budget: number | null; style: string | null; rejectedStyles: string[] };
export type V3Relation = { type: string; subjectId: string; objectId: string | null; score: number; reason: string; evidence: V3Evidence<true>; updatedAt: string };
export type V3Recommendation = { id: string; status: "solution" | "abstain"; offerIds: number[]; styleScore: number | null; confidenceScore: number | null; reasons: string[]; traceId: string };
export type V3Feedback = { recommendationId: string; code: string; note: string; createdAt: string };
export type V3BenchmarkCase = { id: string; version: string; expectedStatus: "solution" | "abstain"; requiredEvidence: string[] };

export type V3PipelineStage = "INTENT" | "CONSTRAINTS" | "RETRIEVAL" | "FILTERING" | "UNDERSTANDING" | "COMPOSITION" | "CRITIC" | "RANKING" | "OPTIMIZATION" | "CONFIDENCE" | "RESPONSE";
export type V3PipelineTrace = { traceId: string; stages: Array<{ stage: V3PipelineStage; status: "completed" | "skipped" | "abstained"; reason: string }> };

export function snapshotCoreOffer(offer: FilonOffer, observedAt: string | null = offer.observedAt ?? null, now: number | Date = Date.now()): V3CoreOffer {
  const normalizedObservedAt = normalizeFilonObservedAt(observedAt);
  const evidenceCurrent = offer.evidenceCurrent === true && isFilonObservationFresh(normalizedObservedAt, now);
  const currentStock = currentFilonStock({ ...offer, observedAt: normalizedObservedAt }, now);
  const unknown = { value: null, status: "unknown" as const, confidence: "low" as const, source: "unavailable" as const, observedAt: normalizedObservedAt };
  const availability: V3Evidence<boolean> = currentStock === null
    ? { ...unknown, rationale: "Disponibilité sans snapshot courant explicite dans le catalogue Core." }
    : { value: currentStock, status: "verified", confidence: "high", source: "catalogue_partner", rationale: "Disponibilité reliée au snapshot Core courant.", observedAt: normalizedObservedAt };
  const price: V3Evidence<number> = evidenceCurrent
    ? { value: offer.price, status: "verified", confidence: "high", source: "catalogue_partner", rationale: "Prix relié au snapshot Core courant.", observedAt: normalizedObservedAt }
    : { ...unknown, rationale: "Prix sans snapshot courant explicite dans le catalogue Core." };
  return { offerId: offer.id, name: offer.name, price, currency: offer.currency, availability, merchantName: offer.merchantName, merchantSlug: offer.merchantSlug, imageUrl: offer.imageUrl, link: offer.link };
}

export function createV3PipelineTrace(traceId: string): V3PipelineTrace {
  const stages: V3PipelineStage[] = ["INTENT", "CONSTRAINTS", "RETRIEVAL", "FILTERING", "UNDERSTANDING", "COMPOSITION", "CRITIC", "RANKING", "OPTIMIZATION", "CONFIDENCE", "RESPONSE"];
  return { traceId, stages: stages.map((stage) => ({ stage, status: "skipped", reason: "En attente." })) };
}

export function updateV3PipelineStage(trace: V3PipelineTrace, stage: V3PipelineStage, status: "completed" | "skipped" | "abstained", reason: string): V3PipelineTrace {
  return { ...trace, stages: trace.stages.map((item) => item.stage === stage ? { ...item, status, reason: reason.slice(0, 240) } : item) };
}
