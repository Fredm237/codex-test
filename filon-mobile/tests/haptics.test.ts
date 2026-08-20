import { describe, expect, it } from "vitest";

import { hapticActionFor } from "../lib/haptic-rules";

describe("haptic action routing", () => {
  it("reserves strong feedback for meaningful confirmation and failure", () => {
    expect(hapticActionFor("primary")).toBe("light");
    expect(hapticActionFor("saved-change")).toBe("medium");
    expect(hapticActionFor("scan-match")).toBe("success");
    expect(hapticActionFor("sync-success")).toBe("success");
    expect(hapticActionFor("failure")).toBe("error");
  });
});
