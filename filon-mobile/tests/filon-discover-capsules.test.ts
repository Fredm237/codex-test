import { describe, expect, it } from "vitest";

import { findDiscoverCapsule, localizedDiscoverCapsuleQuery, selectDiscoverCapsules } from "../lib/filon-discover-capsules";

describe("Capsules Discover FILON", () => {
  it("priorise la direction de style déclarée sans la faire passer pour une offre", () => {
    const capsules = selectDiscoverCapsules({ primary: "classic", confidence: "high", evidenceCount: 1, source: "declared" });
    expect(capsules[0].style).toBe("classic");
    expect(localizedDiscoverCapsuleQuery(capsules[0].id, "fr")).toContain("blazer");
  });

  it("retourne uniquement une capsule connue", () => {
    expect(findDiscoverCapsule("minimal-work")?.occasion).toBe("work");
    expect(findDiscoverCapsule("unknown")).toBeNull();
  });

  it("provides a complete query for every capsule in FR, NL and EN", () => {
    const ids = selectDiscoverCapsules({ primary: null, confidence: "low", evidenceCount: 0, source: "unknown" }, 6).map((capsule) => capsule.id);
    expect(ids).toHaveLength(6);
    for (const locale of ["fr", "nl", "en"] as const) {
      expect(ids.map((id) => localizedDiscoverCapsuleQuery(id, locale)).every((query) => query.trim().split(/\s+/).length >= 3)).toBe(true);
    }
    expect(new Set(ids.map((id) => localizedDiscoverCapsuleQuery(id, "fr"))).size).toBe(6);
    expect(new Set(ids.map((id) => localizedDiscoverCapsuleQuery(id, "nl"))).size).toBe(6);
    expect(new Set(ids.map((id) => localizedDiscoverCapsuleQuery(id, "en"))).size).toBe(6);
  });

  it("retains the semantic capsule state while its visible query follows locale changes", () => {
    const capsule = findDiscoverCapsule("minimal-work");
    if (!capsule) throw new Error("known capsule missing");
    const retained = { id: capsule.id, occasion: capsule.occasion };
    expect(localizedDiscoverCapsuleQuery(retained.id, "fr")).toBe("chemise blanche pantalon droit chaussures cuir");
    expect(localizedDiscoverCapsuleQuery(retained.id, "nl")).toBe("wit overhemd rechte broek leren schoenen");
    expect(localizedDiscoverCapsuleQuery(retained.id, "en")).toBe("white shirt straight trousers leather shoes");
    expect(retained).toEqual({ id: "minimal-work", occasion: "work" });
  });
});
