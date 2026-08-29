import { describe, expect, it } from "vitest";

const projectId = process.env.EXPO_PUBLIC_EAS_PROJECT_ID;

describe.skipIf(!projectId)("Expo push project configuration", () => {
  it("exposes a valid EAS project UUID when remote push is configured", () => {
    expect(projectId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });
});
