import { describe, expect, it } from "vitest";

import { categoryCoverageLabel, topCoveredCategories } from "../lib/category-coverage";

describe("catalogue coverage", () => {
  const items = [{ name: "Informatique", slug: "informatique", count: 40 }, { name: "Téléphonie", slug: "telephonie", count: 90 }, { name: "Empty", slug: "empty", count: 0 }];
  it("keeps only factual positive coverage ordered by offer count", () => { expect(topCoveredCategories(items, 2).map((item) => item.slug)).toEqual(["telephonie", "informatique"]); });
  it("localizes known catalogue departments without changing their data", () => { expect(categoryCoverageLabel(items[0], "en")).toBe("Computers"); });
});
