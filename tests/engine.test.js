import { test } from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULTS,
  CORES,
  adcCode,
  classify,
  timing,
  pathFor,
  sampleAt,
  createRng,
  validateConfig,
  parseSession,
  csvRows,
} from "../simulator/engine.js";
test("ADC endpoints, midpoint rounding and inclusive boundaries", () => {
  assert.equal(adcCode(0), 0);
  assert.equal(adcCode(3.3), 4095);
  assert.equal(adcCode(1.65), 2048);
  for (const code of [800, 3200])
    assert.equal(classify(code, 800, 3200), "safe");
  assert.equal(classify(799, 800, 3200), "low");
  assert.equal(classify(3201, 800, 3200), "high");
  assert.throws(() => adcCode(NaN));
  assert.throws(() => adcCode(4));
});
test("timing accounts for the exact executed instruction path", () => {
  for (const status of ["safe", "high", "low"]) {
    const t = timing(status, DEFAULTS);
    assert.equal(t.instructions, pathFor(status).length);
    assert.equal(
      t.cycles,
      t.costs.reduce((a, b) => a + b),
    );
    assert.ok(t.detectionNs < t.executionNs + DEFAULTS.gpioNs);
    assert.equal(t.executionNs, (t.cycles * 1000) / 72);
  }
  assert.equal(timing("safe", DEFAULTS).cycles, 16);
  assert.equal(timing("high", DEFAULTS).cycles, 14);
  assert.equal(timing("low", DEFAULTS).cycles, 18);
});
test("core clock affects modeled time without treating clocks as core maxima", () => {
  const a = timing("safe", { ...DEFAULTS, core: "m0", clockMHz: 32 }),
    b = timing("safe", { ...DEFAULTS, core: "m4", clockMHz: 168 });
  assert.equal(a.cycles, b.cycles);
  assert.ok(a.executionNs > b.executionNs);
  assert.equal(a.irqNs, 500);
  assert.ok(Math.abs(b.irqNs - 71.428571) < 0.001);
});
test("seeded sampling is reproducible and voltage/code remain bounded", () => {
  const a = createRng(42),
    b = createRng(42);
  for (let i = 0; i < 200; i++) {
    const one = sampleAt(i, DEFAULTS, a),
      two = sampleAt(i, DEFAULTS, b);
    assert.deepEqual(one, two);
    assert.ok(one.code >= 0 && one.code <= 4095);
    assert.ok(one.voltage >= 0 && one.voltage <= 3.3);
  }
  assert.equal(
    sampleAt(0, { ...DEFAULTS, source: "manual", manual: 0 }, a).status,
    "low",
  );
  assert.equal(
    sampleAt(0, { ...DEFAULTS, source: "manual", manual: 4095 }, a).status,
    "high",
  );
});
test("settings reject hostile types, inherited keys and invalid threshold ranges", () => {
  for (const c of [
    { low: 3200, high: 800 },
    { core: "__proto__" },
    { clockMHz: Infinity },
    { source: "<script>" },
    { seed: 0 },
    { low: 2.5 },
    { sampleHz: 0 },
    JSON.parse('{"__proto__":{}}'),
  ])
    assert.throws(() => validateConfig(c));
  assert.throws(() => parseSession('{"version":2}'));
  assert.throws(() => parseSession("x".repeat(100001)));
  assert.deepEqual(
    parseSession(JSON.stringify({ version: 1, config: DEFAULTS })),
    DEFAULTS,
  );
});
test("capture CSV includes the timing conditions used for each sample", () => {
  const row = sampleAt(0, DEFAULTS, createRng(42));
  const csv = csvRows([row]);
  assert.equal(csv.split("\n").length, 2);
  assert.ok(csv.includes("clock_mhz"));
  assert.ok(csv.includes(",m3,72,800,3200,2"));
});
