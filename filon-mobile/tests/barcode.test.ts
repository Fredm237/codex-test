import { describe, expect, it } from "vitest";

import { normalizeProductCode } from "../lib/barcode";

describe("FILON product code parsing", () => {
  it("accepts supported retail codes after formatting cleanup", () => expect(normalizeProductCode("87 19295-43943 4")).toBe("8719295439434"));
  it("rejects values that cannot identify a retail product", () => expect(normalizeProductCode("filon-test")).toBeNull());
});
