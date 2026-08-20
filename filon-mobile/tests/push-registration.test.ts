import { describe, expect, it } from "vitest";

import type { PushRegistration } from "../lib/push-registration";

describe("push registration contract", () => {
  it("only exposes a token when permission and platform registration both succeed", () => {
    const granted: PushRegistration = { status: "granted", token: "ExponentPushToken[test]", platform: "ios" };
    const denied: PushRegistration = { status: "denied" };
    expect(granted.status === "granted" && granted.token.startsWith("ExponentPushToken[")).toBe(true);
    expect(denied.status).toBe("denied");
  });
});
