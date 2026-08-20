import { describe, expect, it } from "vitest";
import { deriveObservedPriceSignal } from "../lib/observed-price";

describe("observed price signals", () => {
  it("uses only two dated observations and reports a decrease", () => { expect(deriveObservedPriceSignal([{ price: 100, at: "2026-01-01T00:00:00Z" }, { price: 85, at: "2026-01-02T00:00:00Z" }])).toMatchObject({ kind: "down", delta: 15 }); });
  it("refuses to infer a movement from insufficient or undated history", () => { expect(deriveObservedPriceSignal([{ price: 100, at: null }, { price: 80, at: "2026-01-02" }]).kind).toBe("insufficient"); });
});
