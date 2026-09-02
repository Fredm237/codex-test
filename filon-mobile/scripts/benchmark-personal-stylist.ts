import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { FilonOffer } from "../lib/filon-api";
import { buildPersonalStylistDecision, type PersonalStylistBrief, type StylistCatalogueCandidate, type StylistWeather } from "../lib/filon-personal-stylist";
import { createWardrobeItem } from "../lib/filon-wardrobe";

type Role = "base" | "structure" | "footwear";
type Case = {
  id: string;
  brief?: Partial<PersonalStylistBrief>;
  weather?: Partial<StylistWeather> | null;
  wardrobe_roles: Role[];
  candidates: { role: Role; price: number; size?: string; stale?: boolean; unsafe?: boolean }[];
  expected_status: "solution" | "abstain";
  expected_reason?: string;
  expected_purchases?: number;
  expected_looks?: number;
};

const NOW = new Date("2026-09-02T12:00:00.000Z");
const DEFAULT_BRIEF: PersonalStylistBrief = { occasion: "work", occasionAt: "2026-09-02T18:00:00.000Z", location: "Bruxelles", style: "classic", budget: 160, requestedSize: "M" };
const DEFAULT_WEATHER: StylistWeather = { location: "Bruxelles", observedAt: "2026-09-02T10:00:00.000Z", validFor: "2026-09-02T18:00:00.000Z", temperatureC: 18, precipitation: "none", source: "trusted_provider" };
const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const cases = JSON.parse(readFileSync(join(root, "quality", "personal-stylist-v1-cases.json"), "utf8")) as Case[];

function offer(id: number, sample: Case["candidates"][number]): FilonOffer {
  return { id, name: `${sample.role}-${id}`, brand: null, category: "Mode", price: sample.price, currency: "EUR", inStock: true, observedAt: sample.stale ? "2026-08-20T00:00:00.000Z" : "2026-09-01T12:00:00.000Z", evidenceCurrent: true, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: sample.unsafe ? "javascript:alert(1)" : `https://example.com/${id}` };
}

const outcomes = cases.map((sample) => {
  const wardrobe = sample.wardrobe_roles.map((role, index) => createWardrobeItem({ label: `${role}-${index}`, role }, `${sample.id}-${index}`, "2026-09-01T00:00:00.000Z")!);
  const candidates: StylistCatalogueCandidate[] = sample.candidates.map((candidate, index) => ({ offer: offer(index + 1, candidate), role: candidate.role, roleEvidence: "product_ontology", size: candidate.size ?? "M", sizeEvidence: "merchant_variant" }));
  const weather = sample.weather === null ? null : { ...DEFAULT_WEATHER, ...(sample.weather ?? {}) };
  const result = buildPersonalStylistDecision({ ...DEFAULT_BRIEF, ...(sample.brief ?? {}) }, wardrobe, weather, candidates, NOW);
  const purchases = result.status === "solution" ? result.looks[0].pieces.filter((piece) => piece.source === "catalogue").length : null;
  const passed = result.status === sample.expected_status
    && (result.status !== "abstain" || result.reason === sample.expected_reason)
    && (sample.expected_purchases === undefined || purchases === sample.expected_purchases)
    && (sample.expected_looks === undefined || (result.status === "solution" && result.looks.length === sample.expected_looks))
    && (result.status !== "solution" || result.looks.every((look) => look.compatibilityScore === null));
  return { case_id: sample.id, passed };
});

const passed = outcomes.filter((outcome) => outcome.passed).length;
const result = { benchmark: "personal-stylist-v1", cases: cases.length, passed, pass_rate: passed / cases.length, false_solutions: outcomes.filter((outcome, index) => !outcome.passed && cases[index].expected_status === "abstain").length, compatibility_scores_published: 0 };
process.stdout.write(`${JSON.stringify(result)}\n`);
if (passed !== cases.length) process.exitCode = 1;
