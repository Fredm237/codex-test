import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";

import type { PushRegistration } from "../lib/push-registration";
import { confirmPushRegistration } from "../lib/push-sync";

describe("push registration contract", () => {
  it("only exposes a token when permission and platform registration both succeed", () => {
    const granted: PushRegistration = { status: "granted", token: "ExponentPushToken[test]", platform: "ios" };
    const denied: PushRegistration = { status: "denied" };
    expect(granted.status === "granted" && granted.token.startsWith("ExponentPushToken[")).toBe(true);
    expect(denied.status).toBe("denied");
  });

  it("reports granted only after the device token reaches the server", async () => {
    const registerDevice = vi.fn(async () => ({ ok: true }));
    await expect(confirmPushRegistration({ status: "granted", token: "ExponentPushToken[test]", platform: "ios" }, registerDevice)).resolves.toBe("granted");
    expect(registerDevice).toHaveBeenCalledWith({ expoToken: "ExponentPushToken[test]", platform: "ios", permission: "granted" });
  });

  it("propagates a server registration failure instead of announcing success", async () => {
    const registerDevice = vi.fn(async () => { throw new Error("offline"); });
    await expect(confirmPushRegistration({ status: "granted", token: "ExponentPushToken[test]", platform: "android" }, registerDevice)).rejects.toThrow("offline");
  });

  it("keeps denied distinct from unavailable in the saved-items UI", async () => {
    const registerDevice = vi.fn(async () => ({ ok: true }));
    await expect(confirmPushRegistration({ status: "denied" }, registerDevice)).resolves.toBe("denied");
    expect(registerDevice).not.toHaveBeenCalled();
    const saved = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "app", "(tabs)", "saved.tsx"), "utf8");
    expect(saved).toContain('pushState === "denied" ? copy.pushDenied');
    expect(saved).not.toContain('pushState === "denied" ? copy.pushUnavailable');
  });
});
