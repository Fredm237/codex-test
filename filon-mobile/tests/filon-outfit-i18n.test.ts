import { describe, expect, it } from "vitest";

import {
  OUTFIT_PUBLIC_MESSAGE_CODES,
  OUTFIT_PUBLIC_MESSAGE_TEMPLATES,
  resolveOutfitPublicMessage,
  type OutfitPublicMessage,
  type OutfitPublicMessageCode,
} from "../lib/filon-outfit-i18n";

const examples = {
  "piece.role_inferred": { code: "piece.role_inferred" },
  "piece.role_unconfirmed": { code: "piece.role_unconfirmed" },
  "recommendation.no_eligible_offers": { code: "recommendation.no_eligible_offers" },
  "recommendation.no_comparable_currency": { code: "recommendation.no_comparable_currency" },
  "recommendation.budget_exceeded": { code: "recommendation.budget_exceeded" },
  "recommendation.evidence_expired": { code: "recommendation.evidence_expired" },
  "score.not_measured": { code: "score.not_measured" },
  "constraint.catalogue_current_offers": { code: "constraint.catalogue_current_offers" },
  "constraint.single_currency": { code: "constraint.single_currency", currency: "EUR" },
  "constraint.budget_unspecified": { code: "constraint.budget_unspecified" },
  "constraint.budget_respected": { code: "constraint.budget_respected", amount: 220, currency: "EUR" },
  "constraint.context_declared": { code: "constraint.context_declared", occasion: "work" },
  "constraint.context_unspecified": { code: "constraint.context_unspecified" },
  "constraint.season_declared": { code: "constraint.season_declared", season: "summer" },
  "constraint.season_unspecified": { code: "constraint.season_unspecified" },
  "constraint.owned_piece": { code: "constraint.owned_piece", label: "navy blazer" },
  "strategy.safe": { code: "strategy.safe" },
  "strategy.signature": { code: "strategy.signature" },
  "strategy.statement": { code: "strategy.statement" },
  "complete.insufficient_current_pieces": { code: "complete.insufficient_current_pieces" },
  "optimization.invalid_snapshot": { code: "optimization.invalid_snapshot" },
  "optimization.no_documented_alternative": { code: "optimization.no_documented_alternative" },
  "optimization.unavailable": { code: "optimization.unavailable" },
  "optimization.evidence_expired": { code: "optimization.evidence_expired" },
  "constraint.optimization_current_offers": { code: "constraint.optimization_current_offers" },
  "constraint.saved_price_historical": { code: "constraint.saved_price_historical" },
  "constraint.unknown_costs_excluded": { code: "constraint.unknown_costs_excluded" },
  "ledger.intent": { code: "ledger.intent", value: "civil wedding" },
  "ledger.policy.offer_classification": { code: "ledger.policy.offer_classification" },
  "ledger.policy.no_commercial_priority": { code: "ledger.policy.no_commercial_priority" },
  "rotation.saved_today": { code: "rotation.saved_today" },
  "rotation.saved_days_ago": { code: "rotation.saved_days_ago", days: 46 },
  "recreate.certain": { code: "recreate.certain" },
  "recreate.probable": { code: "recreate.probable" },
  "recreate.unknown": { code: "recreate.unknown" },
} satisfies Record<OutfitPublicMessageCode, OutfitPublicMessage>;

describe("i18n public du parcours Outfit", () => {
  it("conserve exactement les mêmes clés en français, néerlandais et anglais", () => {
    const expected = [...OUTFIT_PUBLIC_MESSAGE_CODES].sort();
    expect(Object.keys(OUTFIT_PUBLIC_MESSAGE_TEMPLATES.fr).sort()).toEqual(expected);
    expect(Object.keys(OUTFIT_PUBLIC_MESSAGE_TEMPLATES.nl).sort()).toEqual(expected);
    expect(Object.keys(OUTFIT_PUBLIC_MESSAGE_TEMPLATES.en).sort()).toEqual(expected);
    expect(Object.keys(examples).sort()).toEqual(expected);
  });

  it.each(["fr", "nl", "en"] as const)("résout chaque message et chaque paramètre en %s", (locale) => {
    for (const code of OUTFIT_PUBLIC_MESSAGE_CODES) {
      const message = examples[code];
      expect(message.code).toBe(code);
      const resolved = resolveOutfitPublicMessage(message, locale);
      expect(resolved.trim().length).toBeGreaterThan(0);
      expect(resolved).not.toMatch(/\{[a-z]+\}/i);
    }
  });

  it("localise les paramètres numériques et les messages sensibles", () => {
    const budget = examples["constraint.budget_respected"];
    expect(resolveOutfitPublicMessage(budget, "fr")).toMatch(/220.*€/);
    expect(resolveOutfitPublicMessage(budget, "nl")).toMatch(/€.*220|220.*€/);
    expect(resolveOutfitPublicMessage(examples["rotation.saved_days_ago"], "en")).toContain("46");
    expect(resolveOutfitPublicMessage({ code: "rotation.saved_days_ago", days: 1 }, "fr")).toContain("1 jour :");
    expect(resolveOutfitPublicMessage({ code: "rotation.saved_days_ago", days: 2 }, "nl")).toContain("2 dagen");
    expect(resolveOutfitPublicMessage(examples["recreate.unknown"], "fr")).toContain("ambigu");
    expect(resolveOutfitPublicMessage(examples["recreate.unknown"], "nl")).toContain("dubbelzinnig");
    expect(resolveOutfitPublicMessage(examples["recreate.unknown"], "en")).toContain("ambiguous");
  });

  it("conserve les codes sémantiques quand la langue change avec un état existant", () => {
    const context: OutfitPublicMessage = { code: "constraint.context_declared", occasion: "wedding" };
    const season: OutfitPublicMessage = { code: "constraint.season_declared", season: "summer" };
    expect(resolveOutfitPublicMessage(context, "fr")).toBe("Contexte déclaré : Mariage");
    expect(resolveOutfitPublicMessage(context, "nl")).toBe("Opgegeven context: Huwelijk");
    expect(resolveOutfitPublicMessage(context, "en")).toBe("Declared context: Wedding");
    expect(resolveOutfitPublicMessage(season, "fr")).toBe("Saison déclarée : Été");
    expect(resolveOutfitPublicMessage(season, "nl")).toBe("Opgegeven seizoen: Zomer");
    expect(resolveOutfitPublicMessage(season, "en")).toBe("Declared season: Summer");
  });
});
