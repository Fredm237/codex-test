import { describe, expect, it } from "vitest";

import { buildProductComparisonShareText } from "../lib/product-share";

describe("verified comparison sharing", () => {
  const product = { name: "Headphones", ean: "8710398622930", priceMin: 189.99, currency: "EUR", offersCount: 2, merchantsCount: 2 };
  it("keeps French sharing factual and names the evidence limits", () => {
    const text = buildProductComparisonShareText(product, "fr");
    expect(text).toContain("Prix le plus bas observé");
    expect(text).toContain("à confirmer");
    expect(text).not.toContain("meilleur prix");
  });
  it("localizes the comparison message", () => {
    expect(buildProductComparisonShareText(product, "en")).toContain("Lowest observed price");
    expect(buildProductComparisonShareText(product, "nl")).toContain("Laagste waargenomen prijs");
  });
});
