/** Educational timing model, not an ARM emulator or hardware benchmark. */
export const CORES = Object.freeze({
  m0: { name: "Cortex-M0", irqCycles: 16, defaultMHz: 32, isa: "ARMv6-M" },
  m0p: { name: "Cortex-M0+", irqCycles: 15, defaultMHz: 48, isa: "ARMv6-M" },
  m3: { name: "Cortex-M3", irqCycles: 12, defaultMHz: 72, isa: "ARMv7-M" },
  m4: { name: "Cortex-M4", irqCycles: 12, defaultMHz: 168, isa: "ARMv7E-M" },
});
export const DEFAULTS = Object.freeze({
  core: "m3",
  clockMHz: 72,
  low: 800,
  high: 3200,
  sampleHz: 2,
  signalHz: 0.2,
  noise: 80,
  manual: 2048,
  source: "sine",
  loadCycles: 2,
  storeCycles: 2,
  branchCycles: 3,
  gpioNs: 2,
  seed: 42,
});
export const PROGRAM = Object.freeze([
  ["poll", "LDR", "R1, [ADC_DR]", "Read the ADC sample"],
  ["", "LDR", "R2, =T_HIGH", "Load the upper threshold"],
  ["", "CMP", "R1, R2", "Compare unsigned ADC code"],
  ["", "BHI", "alert_high", "Branch if above the upper limit"],
  ["", "LDR", "R3, =T_LOW", "Load the lower threshold"],
  ["", "CMP", "R1, R3", "Compare with the lower limit"],
  ["", "BLO", "alert_low", "Branch if below the lower limit"],
  ["", "MOVS", "R0, #0", "Safe output"],
  ["", "STR", "R0, [GPIO_OUT]", "Write GPIO"],
  ["", "B", "poll", "Repeat polling"],
  ["alert_high", "MOVS", "R0, #1", "High alert output"],
  ["", "STR", "R0, [GPIO_OUT]", "Write GPIO"],
  ["", "B", "poll", "Repeat polling"],
  ["alert_low", "MOVS", "R0, #2", "Low alert output"],
  ["", "STR", "R0, [GPIO_OUT]", "Write GPIO"],
  ["", "B", "poll", "Repeat polling"],
]);
const finite = (v, min, max, name, integer = false) => {
  if (
    typeof v !== "number" ||
    !Number.isFinite(v) ||
    v < min ||
    v > max ||
    (integer && !Number.isInteger(v))
  )
    throw new Error(
      `${name} must be ${integer ? "an integer" : "a number"} from ${min} to ${max}.`,
    );
  return v;
};
export function validateConfig(c) {
  if (!c || typeof c !== "object" || Array.isArray(c))
    throw new Error("Settings must be an object.");
  if (Object.keys(c).some((k) => !Object.hasOwn(DEFAULTS, k)))
    throw new Error("Unknown setting in session.");
  const out = { ...DEFAULTS, ...c };
  if (!Object.hasOwn(CORES, out.core))
    throw new Error("Select a supported Cortex core.");
  if (!["sine", "manual"].includes(out.source))
    throw new Error("Select sine or manual input.");
  for (const [key, min, max, integer] of [
    ["clockMHz", 1, 1000, false],
    ["low", 0, 4095, true],
    ["high", 0, 4095, true],
    ["sampleHz", 1, 20, false],
    ["signalHz", 0.01, 10, false],
    ["noise", 0, 1000, true],
    ["manual", 0, 4095, true],
    ["loadCycles", 1, 100, true],
    ["storeCycles", 1, 100, true],
    ["branchCycles", 1, 100, true],
    ["gpioNs", 0, 10000, false],
    ["seed", 1, 4294967295, true],
  ])
    finite(out[key], min, max, key, integer);
  if (out.low >= out.high)
    throw new Error("Lower threshold must be below the upper threshold.");
  return out;
}
export function adcCode(voltage, vref = 3.3, bits = 12) {
  finite(vref, 0.001, 100, "Reference voltage");
  finite(bits, 1, 24, "ADC bits", true);
  finite(voltage, 0, vref, "Input voltage");
  return Math.round((voltage / vref) * (2 ** bits - 1));
}
export function classify(code, low, high) {
  finite(code, 0, 4095, "ADC code", true);
  if (
    !Number.isInteger(low) ||
    !Number.isInteger(high) ||
    low < 0 ||
    high > 4095 ||
    low >= high
  )
    throw new Error("Invalid thresholds.");
  return code > high ? "high" : code < low ? "low" : "safe";
}
export function pathFor(status) {
  if (status === "high") return [0, 1, 2, 3, 10, 11, 12];
  if (status === "low") return [0, 1, 2, 3, 4, 5, 6, 13, 14, 15];
  if (status === "safe") return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
  throw new Error("Unknown alert state.");
}
export function timing(status, config) {
  const c = validateConfig(config),
    path = pathFor(status);
  const costs = path.map((i) => {
    const op = PROGRAM[i][1];
    if (op === "LDR") return c.loadCycles;
    if (op === "STR") return c.storeCycles;
    if (op === "B") return c.branchCycles;
    if (op === "BHI") return status === "high" ? c.branchCycles : 1;
    if (op === "BLO") return status === "low" ? c.branchCycles : 1;
    return 1;
  });
  const cycles = costs.reduce((a, b) => a + b, 0),
    clockNs = 1000 / c.clockMHz,
    executionNs = cycles * clockNs;
  const gpioIndex = path.findIndex((i) => PROGRAM[i][1] === "STR");
  const detectionNs =
    costs.slice(0, gpioIndex + 1).reduce((a, b) => a + b, 0) * clockNs +
    c.gpioNs;
  return {
    path,
    costs,
    instructions: path.length,
    cycles,
    clockNs,
    executionNs,
    detectionNs,
    samplingWorstNs: 1e9 / c.sampleHz + detectionNs,
    irqNs: CORES[c.core].irqCycles * clockNs,
    activeFraction: (executionNs / (1e9 / c.sampleHz)) * 100,
  };
}
export function createRng(seed) {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(1664525, value) + 1013904223) >>> 0;
    return value / 4294967296;
  };
}
export function sampleAt(index, config, rng, elapsed = null) {
  const c = validateConfig(config);
  finite(index, 0, 1e9, "Sample index", true);
  const seconds =
    elapsed === null
      ? index / c.sampleHz
      : finite(elapsed, 0, 1e12, "Sample time");
  const code =
    c.source === "manual"
      ? c.manual
      : Math.max(
          0,
          Math.min(
            4095,
            Math.round(
              2047.5 +
                1700 * Math.sin(2 * Math.PI * c.signalHz * seconds) +
                (rng() - 0.5) * 2 * c.noise,
            ),
          ),
        );
  const status = classify(code, c.low, c.high);
  return {
    index,
    time: seconds,
    code,
    voltage: (code / 4095) * 3.3,
    status,
    core: c.core,
    clockMHz: c.clockMHz,
    low: c.low,
    high: c.high,
    sampleHz: c.sampleHz,
    ...timing(status, c),
  };
}
export function parseSession(text) {
  if (text.length > 100000) throw new Error("Session file is too large.");
  const data = JSON.parse(text);
  if (data?.version !== 1) throw new Error("Unsupported session format.");
  return validateConfig(data.config);
}
export function csvRows(records) {
  return [
    "sample,time_s,adc_code,voltage_v,state,modeled_cycles,modeled_execution_ns,core,clock_mhz,lower_threshold,upper_threshold,sample_hz",
    ...records.map((r) =>
      [
        r.index,
        r.time.toFixed(6),
        r.code,
        r.voltage.toFixed(6),
        r.status,
        r.cycles,
        r.executionNs.toFixed(3),
        r.core,
        r.clockMHz,
        r.low,
        r.high,
        r.sampleHz,
      ].join(","),
    ),
  ].join("\n");
}
