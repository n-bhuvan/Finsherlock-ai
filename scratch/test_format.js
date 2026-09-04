function formatProbability(prob) {
  if (prob === null || prob === undefined || (typeof prob === "string" && prob.trim() === "")) {
    return "0.00%";
  }
  const num = Number(prob);
  if (isNaN(num) || num <= 0) {
    return "0.00%";
  }
  if (num >= 1.0) {
    return "100.00%";
  }

  // Certainty Guard: Never display 100.00% unless raw probability is exactly 1.0
  let formatted = (num * 100).toFixed(2);
  if (formatted === "100.00") {
    formatted = "99.99";
  }

  return `${formatted}%`;
}

const tests = [
  [1.0, "100.00%"],
  [0.99996, "99.99%"],
  [0.9999, "99.99%"],
  [0.99920899, "99.92%"],
  [0.99938607, "99.94%"],
  [0.001, "0.10%"],
  [0.5, "50.00%"],
  [0.0, "0.00%"],
  [null, "0.00%"],
  [undefined, "0.00%"],
  ["", "0.00%"],
  ["invalid", "0.00%"],
];

for (const [input, expected] of tests) {
  const actual = formatProbability(input);
  console.log(`Input: ${input} -> Actual: ${actual} | Expected: ${expected} | Passed: ${actual === expected}`);
  if (actual !== expected) {
    throw new Error(`Failed for ${input}: got ${actual}, expected ${expected}`);
  }
}
console.log("All unit tests passed!");
