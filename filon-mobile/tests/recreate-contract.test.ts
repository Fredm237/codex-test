import { describe, expect, it } from "vitest";

import { explanationForConfidence, isSafeRecreateImageUrl } from "../lib/recreate-contract";

describe("Contrat Recreate", () => {
  it("n’accepte qu’une inspiration HTTPS publique", () => {
    expect(isSafeRecreateImageUrl("https://images.example.com/look.jpg")).toBe(true);
    expect(isSafeRecreateImageUrl("http://images.example.com/look.jpg")).toBe(false);
    expect(isSafeRecreateImageUrl("javascript:alert(1)")).toBe(false);
  });

  it("accepte une image locale encodée sous une limite stricte", () => {
    expect(isSafeRecreateImageUrl("data:image/jpeg;base64,aGVsbG8=")).toBe(true);
    expect(isSafeRecreateImageUrl("data:text/plain;base64,aGVsbG8=")).toBe(false);
  });

  it("conserve une explication calibrée par niveau de confiance", () => {
    expect(explanationForConfidence("certain")).toContain("clairement observable");
    expect(explanationForConfidence("unknown")).toContain("ambigu");
  });
});
