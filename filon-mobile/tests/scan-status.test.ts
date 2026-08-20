import { describe, expect, it } from "vitest";

import { resolveScanLookupState } from "../lib/scan-status";

describe("scan lookup state", () => {
  it("does not present a network failure as an unmatched product", () => {
    expect(resolveScanLookupState(false, true)).toBe("unavailable");
  });

  it("keeps a genuine absent product distinct from service failure", () => {
    expect(resolveScanLookupState(false, false)).toBe("unmatched");
    expect(resolveScanLookupState(true, false)).toBe("idle");
  });
});
