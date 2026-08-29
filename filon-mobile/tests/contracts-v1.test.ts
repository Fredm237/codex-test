import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { normalizeOffer } from "../lib/filon-api";

const contracts = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "contracts", "v1");
const json = (relative: string) => JSON.parse(readFileSync(join(contracts, relative), "utf8"));

describe("FILON contracts v1", () => {
  it("conserve un stock inconnu du snapshot au modèle mobile", () => {
    const manifest = json("manifest.json");
    expect(manifest.contract_version).toBe("1.0.0");
    expect(manifest.compatibility.unknown).toBe("null_is_not_zero_false_or_true");

    const raw = json(manifest.examples.catalog_offer_unknown);
    expect(normalizeOffer(raw).inStock).toBeNull();
  });
});
