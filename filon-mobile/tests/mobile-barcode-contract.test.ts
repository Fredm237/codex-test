import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { normalizeProductCode } from "../lib/barcode";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const json = (path: string) => JSON.parse(readFileSync(join(root, path), "utf8"));

describe("mobile barcode contract v1", () => {
  it("keeps the scan local and reads only the canonical Core route", () => {
    const manifest = json("contracts/mobile-barcode/v1/manifest.json");
    expect(manifest.raw_code_transmitted).toBe(false);
    expect(manifest.shadow_reader).toBe(false);
    expect(manifest.transport).toBe("GET /api/catalog/product/{canonical_gtin}");
  });

  it("passes every adversarial normalization case", () => {
    const cases = json("quality/mobile-barcode-cases.json") as Array<{ input: string; expected: string | null }>;
    expect(cases).toHaveLength(14);
    for (const sample of cases) expect(normalizeProductCode(sample.input)).toBe(sample.expected);
  });
});
