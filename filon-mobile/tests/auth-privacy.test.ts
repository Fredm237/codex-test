import { beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";

const { secureStore } = vi.hoisted(() => ({
  secureStore: new Map<string, string>(),
}));

vi.mock("expo-secure-store", () => ({
  getItemAsync: vi.fn(async (key: string) => secureStore.get(key) ?? null),
  setItemAsync: vi.fn(async (key: string, value: string) => { secureStore.set(key, value); }),
  deleteItemAsync: vi.fn(async (key: string) => { secureStore.delete(key); }),
}));

vi.mock("react-native", () => ({ Platform: { OS: "ios" } }));
vi.mock("../constants/oauth", () => ({
  SESSION_TOKEN_KEY: "filon.test.session-token",
  USER_INFO_KEY: "filon.test.user-info",
  getApiBaseUrl: () => "https://api.example.invalid",
}));

// The module must be loaded after its native storage dependencies are mocked.
// eslint-disable-next-line import/first
import {
  getSessionToken,
  getUserInfo,
  setSessionToken,
  setUserInfo,
} from "../lib/_core/auth";
// The API client shares the mocked platform, storage and OAuth configuration above.
// eslint-disable-next-line import/first
import { apiCall, exchangeOAuthCode } from "../lib/_core/api";

function renderedLogs(spies: ReturnType<typeof vi.spyOn>[]) {
  return spies.flatMap((spy) => spy.mock.calls).flat().map(String).join("\n");
}

function readSource(relativePath: string) {
  return readFileSync(decodeURIComponent(new URL(relativePath, import.meta.url).pathname), "utf8");
}

describe("authentication privacy", () => {
  beforeEach(() => {
    secureStore.clear();
    vi.restoreAllMocks();
  });

  it("never writes a session token or token prefix to logs", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const token = "session-secret-prefix-that-must-not-appear";

    await setSessionToken(token);
    expect(await getSessionToken()).toBe(token);

    const output = renderedLogs([log, error]);
    expect(output).not.toContain(token);
    expect(output).not.toContain(token.slice(0, 20));
  });

  it("never writes user profile fields to logs", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const user = {
      id: 7,
      openId: "private-open-id",
      name: "Private Person",
      email: "private@example.invalid",
      loginMethod: "oauth",
      lastSignedIn: new Date("2026-09-02T00:00:00Z"),
    };

    await setUserInfo(user);
    expect(await getUserInfo()).toMatchObject({ openId: user.openId, email: user.email });

    const output = renderedLogs([log, error]);
    expect(output).not.toContain(user.openId);
    expect(output).not.toContain(user.name);
    expect(output).not.toContain(user.email);
  });

  it("keeps session tokens and serialized profiles out of callback URLs", () => {
    const callbackSource = readSource("../app/oauth/callback.tsx");

    expect(callbackSource).not.toContain("params.sessionToken");
    expect(callbackSource).not.toContain("params.user");
    expect(callbackSource).not.toContain('searchParams.get("sessionToken")');
    expect(callbackSource).not.toContain("atob(params.user)");
    expect(callbackSource).not.toMatch(/console\.(?:log|info|warn|error)/);
  });

  it("sends the one-time authorization code in a POST body, never in a request URL", () => {
    const clientSource = readSource("../lib/_core/api.ts");
    const serverSource = readSource("../server/_core/oauth.ts");

    expect(clientSource).toContain('apiCall<{ app_session_id: string; user: any }>("/api/oauth/mobile"');
    expect(clientSource).toContain('method: "POST"');
    expect(clientSource).not.toContain("/api/oauth/mobile?");
    expect(serverSource).toContain('app.post("/api/oauth/mobile"');
    expect(serverSource).not.toContain('app.get("/api/oauth/mobile"');
  });

  it("exchanges code and state through a POST body without logging either value", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const fetchMock = vi.fn(async (_url: string, _request?: RequestInit) => new Response(JSON.stringify({
      app_session_id: "new-session-token",
      user: null,
    }), { status: 200, headers: { "content-type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(exchangeOAuthCode("private-one-time-code", "private-state")).resolves.toEqual({
      sessionToken: "new-session-token",
      user: null,
    });

    const [url, request] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api.example.invalid/api/oauth/mobile");
    expect(url).not.toContain("private-one-time-code");
    expect(request).toMatchObject({ method: "POST" });
    expect(JSON.parse(String(request?.body))).toEqual({
      code: "private-one-time-code",
      state: "private-state",
    });
    expect(renderedLogs([log, error])).not.toMatch(/private-one-time-code|private-state|new-session-token/);
  });

  it("does not expose an API error body to callers or logs", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.stubGlobal("fetch", vi.fn(async () => new Response(
      "private-provider-diagnostic",
      { status: 401 },
    )));

    await expect(apiCall("/api/private")).rejects.toThrow("API_REQUEST_FAILED_401");
    expect(renderedLogs([log, error])).not.toContain("private-provider-diagnostic");
  });

  it("does not attach raw authentication errors to server logs", () => {
    const sources = [
      "../server/_core/oauth.ts",
      "../server/_core/sdk.ts",
      "../server/db.ts",
      "../constants/oauth.ts",
    ].map(readSource);

    for (const source of sources) {
      expect(source).not.toMatch(/console\.(?:warn|error)\([^;]*(?:,\s*error|String\(error\))/s);
    }
  });
});
