import {
  CORES,
  DEFAULTS,
  PROGRAM,
  validateConfig,
  classify,
  timing,
  createRng,
  sampleAt,
  parseSession,
  csvRows,
} from "./engine.js";
const $ = (id) => document.getElementById(id);
let config = { ...DEFAULTS },
  records = [],
  running = false,
  timer = null,
  elapsed = 0,
  index = 0,
  rng = createRng(config.seed),
  last = sampleAt(0, config, createRng(config.seed)),
  noticeTimer;
const num = (n, d = 1) =>
  n.toLocaleString(undefined, {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function notice(text) {
  $("notice").textContent = text;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => ($("notice").textContent = ""), 4000);
}
function error(text) {
  $("error").textContent = text;
  $("error").hidden = !text;
}
function download(name, type, content) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function syncInputs() {
  for (const key of Object.keys(config)) {
    const input = $(key);
    if (input) input.value = config[key];
  }
  for (const key of ["low", "high", "manual", "noise"])
    $(key + "-value").value = config[key];
  $("manual").disabled = config.source !== "manual";
}
function pause() {
  running = false;
  clearTimeout(timer);
  timer = null;
  $("run").textContent = "Run simulation";
  $("run-status").textContent = "Paused · single sample available";
}
function preview() {
  const code = config.source === "manual" ? config.manual : last.code;
  last = {
    ...sampleAt(0, config, createRng(config.seed), elapsed),
    code,
    voltage: (code / 4095) * 3.3,
    status: classify(code, config.low, config.high),
    ...timing(classify(code, config.low, config.high), config),
  };
  render();
}
function capture() {
  last = sampleAt(index, config, rng, elapsed);
  records.push(last);
  if (records.length > 1000) records.shift();
  index++;
  elapsed += 1 / config.sampleHz;
  render();
}
function schedule() {
  if (!running) return;
  timer = setTimeout(() => {
    capture();
    schedule();
  }, 1000 / config.sampleHz);
}
function reset() {
  pause();
  records = [];
  elapsed = 0;
  index = 0;
  rng = createRng(config.seed);
  last = sampleAt(0, config, createRng(config.seed));
  render();
  notice("Capture reset. The same seed repeats the same signal.");
}
for (const key of Object.keys(config)) {
  const input = $(key);
  if (!input) continue;
  input.addEventListener(
    input.tagName === "SELECT" ? "change" : "input",
    () => {
      const candidate = {
        ...config,
        [key]: ["core", "source"].includes(key)
          ? input.value
          : Number(input.value),
      };
      if (key === "core") candidate.clockMHz = CORES[input.value].defaultMHz;
      try {
        config = validateConfig(candidate);
        error("");
        syncInputs();
        if (key === "seed") rng = createRng(config.seed);
        if (running) {
          clearTimeout(timer);
          schedule();
        }
        preview();
      } catch (e) {
        error(e.message);
      }
    },
  );
  input.addEventListener("blur", syncInputs);
}
$("run").onclick = () => {
  if (running) pause();
  else {
    error("");
    running = true;
    $("run").textContent = "Pause simulation";
    $("run-status").textContent = "Running · generated input";
    capture();
    schedule();
  }
};
$("step").onclick = () => {
  pause();
  capture();
};
$("reset").onclick = () => {
  if (
    index &&
    !confirm(
      "Clear the captured samples? Export CSV first if you want to keep them.",
    )
  )
    return;
  reset();
};
$("export-csv").onclick = () =>
  download("signal-bench-capture.csv", "text/csv", csvRows(records));
$("export-session").onclick = () =>
  download(
    "signal-bench-settings.json",
    "application/json",
    JSON.stringify({ version: 1, config }, null, 2),
  );
$("import-session").onclick = () => $("file").click();
$("file").onchange = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    if (file.size > 100000)
      throw new Error("Choose a settings file smaller than 100 KB.");
    const parsed = parseSession(await file.text());
    if (index && !confirm("Loading settings starts a new capture. Continue?"))
      return;
    config = parsed;
    syncInputs();
    reset();
    error("");
    notice("Settings loaded.");
  } catch (e) {
    error(
      e instanceof SyntaxError ? "This file contains invalid JSON." : e.message,
    );
  }
};
document.addEventListener("visibilitychange", () => {
  if (document.hidden && running) {
    pause();
    notice("Paused while this tab is hidden.");
  }
});
function render() {
  const status = classify(last.code, config.low, config.high),
    t = timing(status, config);
  $("adc").textContent = last.code;
  $("voltage").textContent = num((last.code / 4095) * 3.3, 3) + " V input";
  $("alert").textContent =
    status === "safe" ? "SAFE" : status === "high" ? "HIGH ALERT" : "LOW ALERT";
  $("alert").className = "status " + status;
  $("boundary").textContent =
    status === "safe"
      ? `${config.low} ≤ D ≤ ${config.high}`
      : status === "high"
        ? `D > ${config.high}`
        : `D < ${config.low}`;
  $("sample-count").textContent = `${index} sample${index === 1 ? "" : "s"}`;
  $("export-csv").disabled = !records.length;
  $("path-count").textContent =
    `${t.instructions} instructions · ${t.cycles} modeled cycles`;
  $("assembly").innerHTML = PROGRAM.map(
    ([label, op, args, comment], i) =>
      `${label ? '<div class="asm-label">' + escape(label) + ":</div>" : ""}<div class="code-line ${t.path.includes(i) ? "active" : ""} ${label ? "label" : ""}" title="${escape((label ? label + ": " : "") + comment)}"><span>${t.path.includes(i) ? "→" : ""}</span><em>${op}</em><span>${escape(args)}</span></div>`,
  ).join("");
  const metrics = [
    ["Clock period", num(t.clockNs, 3) + " ns"],
    ["Whole loop path", num(t.executionNs) + " ns"],
    ["ADC read → GPIO write", num(t.detectionNs) + " ns"],
    ["Sampling interval", num(1000 / config.sampleHz) + " ms"],
    ["Sampled detection bound", num(t.samplingWorstNs / 1e6, 4) + " ms"],
    ["Ideal exception entry", num(t.irqNs) + " ns"],
    ["Per-sample work fraction", num(t.activeFraction, 6) + "%"],
  ];
  $("timing").innerHTML = metrics
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
  const nyquist = config.sampleHz >= 2 * config.signalHz;
  $("nyquist").textContent =
    config.source === "manual"
      ? "Manual input: no periodic signal is defined, so no Nyquist conclusion is made."
      : `${nyquist ? "Nyquist condition met" : "Aliasing risk"} for the clean sine: ${config.sampleHz} Hz ${nyquist ? "≥" : "<"} 2 × ${config.signalHz} Hz. Random noise is not band-limited by this model.`;
  renderTrace();
  renderComparison(t);
  renderEquations(t, status);
}
function svgFrame(width, height, content, label) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escape(label)}">${content}</svg>`;
}
function renderTrace() {
  const w = Math.max(300, $("signal-plot").clientWidth),
    h = 255,
    left = 48,
    right = 18,
    top = 20,
    bottom = 40,
    xspan = w - left - right,
    yspan = h - top - bottom;
  const shown = records.slice(-60),
    first = shown[0]?.time ?? 0,
    lastTime = shown.at(-1)?.time ?? 1,
    timeSpan = Math.max(1 / config.sampleHz, lastTime - first);
  const x = (t) => left + ((t - first) / timeSpan) * xspan,
    y = (v) => top + ((4095 - v) / 4095) * yspan;
  let s = [0, 1024, 2048, 3072, 4095]
    .map(
      (value) =>
        `<line x1="${left}" y1="${y(value)}" x2="${w - right}" y2="${y(value)}" stroke="#dce2df"/><text x="${left - 8}" y="${y(value) + 4}" text-anchor="end">${value}</text>`,
    )
    .join("");
  for (const [v, color, label] of [
    [config.low, "#946017", "LOW"],
    [config.high, "#b14539", "HIGH"],
  ])
    s += `<line x1="${left}" y1="${y(v)}" x2="${w - right}" y2="${y(v)}" stroke="${color}" stroke-dasharray="4 4"/><text x="${w - right}" y="${y(v) - 6}" text-anchor="end">${label} ${v}</text>`;
  if (shown.length)
    s += `<polyline points="${shown.map((p) => `${x(p.time)},${y(p.code)}`).join(" ")}" fill="none" stroke="#1e4562" stroke-width="2"/>`;
  for (const p of shown)
    s += `<circle cx="${x(p.time)}" cy="${y(p.code)}" r="3" fill="${p.status === "safe" ? "#38644a" : p.status === "high" ? "#b14539" : "#946017"}"><title>${p.time.toFixed(2)} s: ${p.code} (${p.status})</title></circle>`;
  if (!shown.length)
    s += `<text x="${left + xspan / 2}" y="${top + yspan / 2}" text-anchor="middle">Run or take a single sample to start the trace.</text>`;
  s += `<text x="${left}" y="${h - 15}">${first.toFixed(1)} s</text><text x="${w - right}" y="${h - 15}" text-anchor="end">${(first + timeSpan).toFixed(1)} s</text><text x="${left + xspan / 2}" y="${h - 15}" text-anchor="middle" class="axis-label">Simulated time (s)</text><text x="0" y="12" class="axis-label">ADC code</text>`;
  $("signal-plot").innerHTML = svgFrame(w, h, s, "ADC trace with thresholds");
}
function renderComparison() {
  const w = Math.max(300, $("comparison-plot").clientWidth),
    h = 300,
    left = 100,
    right = 65,
    top = 35,
    bottom = 46;
  const rows = Object.entries(CORES).map(([id, c]) => {
    const cfg = {
      ...config,
      core: id,
      clockMHz: id === config.core ? config.clockMHz : c.defaultMHz,
    };
    return {
      name: c.name,
      mhz: cfg.clockMHz,
      active: id === config.core,
      ...timing(classify(last.code, config.low, config.high), cfg),
    };
  });
  const max = Math.max(...rows.flatMap((r) => [r.executionNs, r.irqNs])) * 1.1,
    x = (v) => left + ((w - left - right) * v) / max;
  let s = `<rect x="${left}" y="10" width="12" height="8" fill="#1e4562"/><text x="${left + 18}" y="18">Polling path</text><rect x="${left + 120}" y="10" width="12" height="8" fill="#abbdb9"/><text x="${left + 138}" y="18">IRQ entry</text>`;
  rows.forEach((r, i) => {
    const y = top + i * 52;
    s += `<text x="${left - 10}" y="${y + 12}" text-anchor="end">${r.name.replace("Cortex-", "")}${r.active ? " *" : ""}</text><text x="${left - 10}" y="${y + 30}" text-anchor="end" class="axis-label">${r.mhz} MHz</text><rect x="${left}" y="${y}" width="${x(r.executionNs) - left}" height="13" fill="#1e4562"/><rect x="${left}" y="${y + 17}" width="${x(r.irqNs) - left}" height="13" fill="#abbdb9"/><text x="${x(r.executionNs) + 5}" y="${y + 11}">${num(r.executionNs)}</text><text x="${x(r.irqNs) + 5}" y="${y + 28}">${num(r.irqNs)}</text>`;
  });
  s += `<line x1="${left}" y1="${h - bottom}" x2="${w - right}" y2="${h - bottom}" stroke="#b9c5c0"/><text x="${left}" y="${h - 24}">0</text><text x="${w - right}" y="${h - 24}" text-anchor="end">${num(max, 0)}</text><text x="${left + (w - left - right) / 2}" y="${h - 7}" text-anchor="middle" class="axis-label">Modeled time (ns) · * selected core</text>`;
  $("comparison-plot").innerHTML = svgFrame(
    w,
    h,
    s,
    "Modeled core comparison, nanoseconds",
  );
}
function renderEquations(t, status) {
  const volts = (last.code / 4095) * 3.3;
  const equations = [
    [
      "01 · ADC conversion",
      "D = round((Vin / Vref) × (2ⁿ − 1))",
      `${num(volts, 3)} / 3.3 × 4095 ≈ ${last.code}`,
    ],
    [
      "02 · Quantization step",
      "LSB = Vref / 2ⁿ",
      `${num((3.3 / 4096) * 1000, 4)} mV per ideal quantization bin`,
    ],
    [
      "03 · Sample frequency",
      "fs = 1 / Ts",
      `1 / ${num(1 / config.sampleHz, 3)} s = ${config.sampleHz} Hz`,
    ],
    [
      "04 · Nyquist condition",
      "fs ≥ 2 × fsignal",
      config.source === "manual"
        ? "Not evaluated for manual input."
        : `${config.sampleHz} Hz vs ${2 * config.signalHz} Hz; applies to the clean sine only.`,
    ],
    [
      "05 · Upper threshold",
      "D > T_HIGH → high",
      `${last.code} > ${config.high}: ${last.code > config.high}`,
    ],
    [
      "06 · Lower threshold",
      "D < T_LOW → low",
      `${last.code} < ${config.low}: ${last.code < config.low}`,
    ],
    [
      "07 · Inclusive safe range",
      "T_LOW ≤ D ≤ T_HIGH",
      status === "safe" ? "Both bounds satisfied." : "Outside the safe range.",
    ],
    [
      "08 · Modeled execution",
      "T_exec = Σ(cost_i) × T_clock",
      `${t.cycles} × ${num(t.clockNs, 3)} ns = ${num(t.executionNs)} ns`,
    ],
    [
      "09 · Detection bound",
      "T_detect ≤ Ts + T_read-to-GPIO",
      `${num(t.samplingWorstNs / 1e6, 4)} ms, assuming a sample opportunity within Ts`,
    ],
    [
      "10 · GPIO modeled response",
      "T_GPIO_response = prefix cycles / fclk + GPIO delay",
      `${num(t.detectionNs)} ns; includes instructions through STR`,
    ],
    [
      "11 · Electrical power",
      "P = V × I",
      "No current is measured or specified. Power is not estimated.",
    ],
    [
      "12 · Per-sample work fraction",
      "work fraction = T_exec / Ts × 100%",
      `${num(t.activeFraction, 6)}%; excludes busy polling and other processor work.`,
    ],
  ];
  $("equations").innerHTML =
    '<div class="equations-grid">' +
    equations
      .map(
        ([title, formula, value]) =>
          `<section class="eq"><h3>${escape(title)}</h3><p>${escape(formula)}</p><span>${escape(value)}</span></section>`,
      )
      .join("") +
    "</div>";
}
new ResizeObserver(() => {
  renderTrace();
  renderComparison();
}).observe($("signal-plot"));
syncInputs();
render();
