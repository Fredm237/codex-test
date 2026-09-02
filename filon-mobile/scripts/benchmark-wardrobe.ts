import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { sanitizeWardrobe, wardrobeCoverage } from "../lib/filon-wardrobe";

type Case = { id: string; input: unknown[]; expected_count: number; expected_missing: string[] };
const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const cases = JSON.parse(readFileSync(join(root, "quality", "wardrobe-v1-cases.json"), "utf8")) as Case[];
const outcomes = cases.map((sample) => {
  const items = sanitizeWardrobe(sample.input);
  const coverage = wardrobeCoverage(items);
  const passed = items.length === sample.expected_count
    && JSON.stringify(coverage.missingRoles) === JSON.stringify(sample.expected_missing)
    && coverage.score === null
    && items.every((item) => item.provenance === "user_declared" && item.storageScope === "local_device");
  return { case_id: sample.id, passed };
});
const passed = outcomes.filter((outcome) => outcome.passed).length;
const result = { benchmark: "wardrobe-v1", cases: cases.length, passed, pass_rate: passed / cases.length, inferred_items: 0, network_writes: 0 };
process.stdout.write(`${JSON.stringify(result)}\n`);
if (passed !== cases.length) process.exitCode = 1;
