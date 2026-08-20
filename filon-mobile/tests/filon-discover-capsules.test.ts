import { describe, expect, it } from "vitest";

import { findDiscoverCapsule, selectDiscoverCapsules } from "../lib/filon-discover-capsules";

describe("Capsules Discover FILON", () => {
  it("priorise la direction de style déclarée sans la faire passer pour une offre", () => {
    const capsules = selectDiscoverCapsules({ primary: "classic", confidence: "high", evidenceCount: 1, source: "declared" });
    expect(capsules[0].style).toBe("classic");
    expect(capsules[0].startQuery).toContain("blazer");
  });

  it("retourne uniquement une capsule connue", () => {
    expect(findDiscoverCapsule("minimal-work")?.occasion).toBe("work");
    expect(findDiscoverCapsule("unknown")).toBeNull();
  });
});
