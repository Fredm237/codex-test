import { describe, expect, it } from "vitest";

const projectId = process.env.EXPO_PUBLIC_EAS_PROJECT_ID;

// Smoke test réseau, activé uniquement dans l'environnement Expo configuré.
describe.skipIf(!projectId)("EAS project linkage", () => {
  it("exposes a public FILON EAS project identifier and reaches its Expo project page", async () => {
    expect(projectId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const response = await fetch("https://expo.dev/accounts/filon237-team/projects/filon", { redirect: "manual" });
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.status).toBeLessThan(400);
  }, 15_000);
});
