import { assertEquals, assertThrows } from "@std/assert";
import { validateEstimates } from "./index.ts";

const request = [{
  id: "food-1",
  time: "12:30",
  description: "test meal",
  memory_id: "",
  photos: [],
}];

function response(overrides: Record<string, unknown> = {}) {
  return {
    entries: [{
      id: "food-1",
      canonical_name: "Test meal",
      memory_eligible: false,
      serving_description: "one serving",
      portion_description: "one serving",
      visual_portion_cues: [],
      portion_basis: "text",
      calories: 900,
      protein_g: 20,
      carbs_g: 30,
      fat_g: 10,
      fiber_g: 5,
      sugar_g: 4,
      added_sugar_g: 0,
      confidence: 0.8,
      assumptions: [],
      ...overrides,
    }],
  };
}

Deno.test("strict validation rejects a calorie and macro mismatch", () => {
  assertThrows(
    () => validateEstimates(response(), request),
    Error,
    "calorie_macro_mismatch",
  );
});

Deno.test("fallback reconciles calories from macros and lowers confidence", () => {
  const [estimate] = validateEstimates(response(), request, {
    reconcileMacroMismatch: true,
  });

  assertEquals(estimate.calories, 290);
  assertEquals(estimate.confidence, 0.55);
  assertEquals(estimate.assumptions.length, 1);
});

Deno.test("consistent estimates remain unchanged", () => {
  const [estimate] = validateEstimates(response({ calories: 300 }), request);

  assertEquals(estimate.calories, 300);
  assertEquals(estimate.confidence, 0.8);
  assertEquals(estimate.assumptions, []);
});
