import { describe, expect, it } from "vitest";

import { normalizeProductCode } from "../lib/barcode";

describe("FILON product code parsing", () => {
  it("accepts supported retail codes after formatting cleanup", () => expect(normalizeProductCode("87 19295-43943 4")).toBe("8719295439434"));
  it("canonicalizes UPC-A to the EAN-13 catalogue key", () => expect(normalizeProductCode("036000291452")).toBe("0036000291452"));
  it("canonicalizes a zero-prefixed GTIN-14 to the EAN-13 catalogue key", () => expect(normalizeProductCode("04006381333931")).toBe("4006381333931"));
  it("keeps a non-zero-prefixed GTIN-14 intact", () => expect(normalizeProductCode("10012345678902")).toBe("10012345678902"));
  it.each([
    "filon-test",
    "4006381333932",
    "0000000000000",
    "11111111",
    "1234567",
    "123456789012345",
  ])("rejects a value that cannot identify a retail product: %s", (value) => {
    expect(normalizeProductCode(value)).toBeNull();
  });
});
