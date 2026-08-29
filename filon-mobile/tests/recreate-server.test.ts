import { beforeEach, describe, expect, it, vi } from "vitest";
import { invokeLLM } from "../server/_core/llm";
import { analyzeRecreateInspiration } from "../server/recreate";

vi.mock("../server/_core/llm", () => ({ invokeLLM: vi.fn() }));

const invoke = vi.mocked(invokeLLM);

describe("Recreate dynamique localisé", () => {
  beforeEach(() => invoke.mockReset());

  it.each([
    ["fr", "Silhouette droite", "Veste visible", "Image partielle"],
    ["nl", "Recht silhouet", "Zichtbare jas", "Gedeeltelijk beeld"],
    ["en", "Straight silhouette", "Visible jacket", "Partial image"],
  ] as const)("propage %s jusqu’au prompt et balise la sortie", async (locale, summary, label, limit) => {
    invoke.mockResolvedValue({
      id: "recreate-test",
      created: 0,
      model: "test",
      choices: [{
        index: 0,
        finish_reason: "stop",
        message: {
          role: "assistant",
          content: JSON.stringify({
            summary,
            silhouette: [{ label, confidence: "certain", explanation: summary }],
            palette: [],
            visiblePieces: [],
            limits: [limit],
          }),
        },
      }],
    });

    const result = await analyzeRecreateInspiration("https://images.example.com/look.jpg", locale);

    expect(result).toMatchObject({ locale, summary, silhouette: [{ label }], limits: [limit] });
    const request = invoke.mock.calls[0][0];
    expect(JSON.stringify(request.messages)).toContain(locale === "fr" ? "français" : locale === "nl" ? "Nederlands" : "English");
  });
});
