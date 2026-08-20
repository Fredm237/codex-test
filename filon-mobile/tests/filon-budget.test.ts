import { describe, expect, it } from "vitest";

import { calculateBudget } from "../lib/filon-budget";

describe("Lecture budgétaire FILON", () => {
  it("calcule un reste sous budget à partir de prix observés", () => {
    expect(calculateBudget(120, 200)).toMatchObject({ spent: 120, remaining: 80, ratio: 0.6, status: "under" });
  });

  it("signale la proximité ou le dépassement sans modifier les prix", () => {
    expect(calculateBudget(95, 100).status).toBe("near_limit");
    expect(calculateBudget(101, 100).status).toBe("over");
  });

  it("ne fabrique aucun budget lorsqu’aucune contrainte n’est déclarée", () => {
    expect(calculateBudget(120, null)).toMatchObject({ remaining: null, status: "no_budget" });
  });
});
