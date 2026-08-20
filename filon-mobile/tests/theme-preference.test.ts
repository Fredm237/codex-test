import { describe, expect, it } from "vitest";

import { resolveAppearance } from "../lib/theme-preference";

describe("FILON appearance preference", () => {
  it("keeps an explicit light or dark preference", () => {
    expect(resolveAppearance("light", "dark")).toBe("light");
    expect(resolveAppearance("dark", "light")).toBe("dark");
  });

  it("follows the system when requested", () => {
    expect(resolveAppearance("system", "light")).toBe("light");
    expect(resolveAppearance("system", "dark")).toBe("dark");
  });
});
