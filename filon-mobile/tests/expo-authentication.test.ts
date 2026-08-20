import { describe, expect, it } from "vitest";

const expoToken = process.env.EXPO_TOKEN;

describe("Expo authentication", () => {
  it("authenticates the configured token against the Expo GraphQL identity endpoint", async () => {
    expect(expoToken).toMatch(/^\S{20,}$/);
    const response = await fetch("https://api.expo.dev/graphql", {
      method: "POST",
      headers: { Authorization: `Bearer ${expoToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ query: "query CurrentUser { meActor { id } }" }),
    });
    expect(response.status).toBe(200);
    const body = await response.json() as { data?: { meActor?: { id?: string } } };
    expect(body.data?.meActor?.id).toMatch(/\S/);
  }, 15_000);
});
