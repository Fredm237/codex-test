import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { normalizeProductCode } from "../lib/barcode";

type Case = { id: string; input: string; expected: string | null };

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const cases = JSON.parse(readFileSync(join(root, "quality", "mobile-barcode-cases.json"), "utf8")) as Case[];
const outcomes = cases.map((sample) => ({ ...sample, actual: normalizeProductCode(sample.input) }));
const passed = outcomes.filter((sample) => sample.actual === sample.expected).length;
const invalid = outcomes.filter((sample) => sample.expected === null);
const falseAccepts = invalid.filter((sample) => sample.actual !== null).length;
const result = {
  benchmark: "mobile-barcode-v1",
  cases: cases.length,
  passed,
  pass_rate: passed / cases.length,
  invalid_cases: invalid.length,
  false_accepts: falseAccepts,
};

process.stdout.write(`${JSON.stringify(result)}\n`);
if (passed !== cases.length || falseAccepts !== 0) process.exitCode = 1;
