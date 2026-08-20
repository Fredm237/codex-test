import { describe, expect, it } from "vitest";

import { notificationOccasionPath, notificationProductPath } from "../lib/notification-route";

describe("notification product routing", () => {
  it("accepts only normalized EAN/UPC payloads", () => {
    expect(notificationProductPath({ ean: "8710398622930" })).toBe("/product/ean/8710398622930");
    expect(notificationProductPath({ ean: "abc" })).toBeNull();
    expect(notificationProductPath({ url: "/settings" })).toBeNull();
  });

  it("accepte uniquement un identifiant d’occasion local sûr", () => {
    expect(notificationOccasionPath({ occasionId: "1723824000000-abc123" })).toBe("/outfit-studio?occasionId=1723824000000-abc123");
    expect(notificationOccasionPath({ occasionId: "/settings" })).toBeNull();
  });
});
