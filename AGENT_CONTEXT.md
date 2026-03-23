# AGENT_CONTEXT.md
# ARM Sensor Threshold Alert Simulator — Agent Regeneration File
# Version 2 — Live Per-Core Graphs + Anti-Gravity Theme

This file contains everything an AI agent needs to fully recreate the ARM Cortex-M
Sensor Threshold Alert Simulator from scratch as a standalone Chrome HTML file.

Paste the prompt in the AGENT PROMPT section into a new Claude chat.
Claude will output one complete `.html` file. Save it, double-click, open in Chrome.

---

## AESTHETIC DIRECTION — ANTI-GRAVITY / SPACE STATION

- **Background:** `#07080f` with repeating scan-line overlay (1px horizontal lines at
  1.5% white opacity using `repeating-linear-gradient`)
- **Panels:** `rgba(255,255,255,0.04)` background, `backdrop-filter: blur(12px)`,
  `1px solid rgba(0,212,255,0.18)` border, `border-radius: 6px`
- **Accent colors:**
  - Ion blue: `#00d4ff` — selected state, active ASM lines, borders
  - Plasma green: `#00ff9f` — safe state, positive values, M4
  - Alert amber: `#ffaa00` — low threshold, M0+
  - Danger red: `#ff3b5c` — high alert, critical state, M0
  - Dim white: `rgba(255,255,255,0.4)` — secondary labels
- **Fonts:** `Orbitron` (700 weight) for all labels, headings, badges.
  `Share Tech Mono` for all data values, numbers, assembly code.
  Import both from Google Fonts.
- **Float animations:** Every panel gets a unique `@keyframes` sinusoidal vertical
  drift (±3–5px, 6–9 second period) using `transform: translateY` only.
  Each panel has a different animation-delay so they drift independently.
- **Glow effects:** Active assembly lines use `box-shadow: inset 2px 0 0 [color]`
  instead of background-color. LEDs use pulsing radial `box-shadow` bloom.
  Selected core cards use `box-shadow: 0 0 15px [coreColor]40`.
- **Title shimmer:** App title uses `background: linear-gradient(90deg, ion, plasma, ion)`
  with `background-size: 200%` and `animation: shimmer 4s linear infinite` using
  `background-position` keyframes. Apply via `-webkit-background-clip: text`.
- **Live indicator dots:** Small 6px circles with pulsing glow animation, one per
  graph panel header, color matches selected core.
- **No gradients on surfaces.** No rounded corners larger than 6px.
- **Chart styling:** All chart canvas backgrounds transparent. Grid lines at
  `rgba(0,212,255,0.07)`. Tick labels in `rgba(255,255,255,0.35)`.

---

## AGENT PROMPT

```
Build a single complete HTML file (DOCTYPE included) — no frameworks, vanilla JS,
Chart.js 4.4.1 from cdnjs.cloudflare.com. The file must open by double-clicking in Chrome.

This is an ARM Cortex-M Sensor Data Acquisition and Threshold Alert System Simulator
for a university microprocessors research paper.

════════════════════════════════════════════════
AESTHETIC: ANTI-GRAVITY / SPACE STATION PANEL
════════════════════════════════════════════════

Background #07080f + scan-line CSS overlay at 1.5% opacity.
All panels: rgba(255,255,255,0.04) bg, backdrop-filter blur(12px),
1px solid rgba(0,212,255,0.18) border, border-radius 6px.

Colors:
  --ion:    #00d4ff   (selected, active, borders)
  --plasma: #00ff9f   (safe, M4)
  --amber:  #ffaa00   (low alert, M0+)
  --danger: #ff3b5c   (high alert, M0)
  --dim:    rgba(255,255,255,0.4)

Fonts: @import Orbitron:700 and Share Tech Mono from Google Fonts.
  Orbitron for ALL labels, headings, button text, badges.
  Share Tech Mono for ALL data values, numbers, assembly code.

Animations:
  - 4 unique @keyframes float animations (translateY ±3–5px, 6–9s periods).
    Assign each panel a different one + animation-delay so they drift independently.
  - App title: shimmer animation using background-clip text with ion→plasma→ion gradient.
  - LEDs: pulsing box-shadow bloom (pulse-safe=plasma, pulse-danger=danger, pulse-amber=amber).
  - Active ASM lines: box-shadow inset glow, NOT background-color.
  - Live dot indicators in graph headers: 6px circles with pulse animation.

Charts:
  Canvas backgrounds transparent. Grid rgba(0,212,255,0.07). Ticks rgba(255,255,255,0.35).
  Font: Share Tech Mono 9px.
  Core bar colors: M0=#ff3b5c  M0+=#ffaa00  M3=#00d4ff  M4=#00ff9f

════════════════════════════════════════════════
LAYOUT — FULL PAGE
════════════════════════════════════════════════

TOP BAR (always visible, no float):
  Left: App title "ARM CORTEX-M · SENSOR ALERT · LIVE" with shimmer
  Center: Core tabs — M0 / M0+ / M3 / M4 (default M3 selected)
    Each tab uses the core's color when selected (M0=danger, M0+=amber, M3=ion, M4=plasma)
  Right: Status pill (RUNNING=plasma / HALTED=danger) + RUN/STOP button

CORE INFO BAR (full width, below top bar, above main layout):
  4 cards side by side, one per core.
  Selected card: border = core color, box-shadow glow in core color.
  Each card shows: core name (in core color), IRQ cycles (green if 12 / red if 16),
  clock speed, latency (green if <200ns / red if >400ns), T_clock in ns.
  Clicking a card selects that core (same as tab).

MAIN LAYOUT: CSS grid, 2 equal columns, gap 12px.

════════════════════════════════════════════════
LEFT COLUMN — LIVE SIMULATION
════════════════════════════════════════════════

CONTROLS (no float):
  Row 1: T_LOW slider (100–1500, default 800) and T_HIGH slider (1500–4000, default 3200).
    Labels show live value. Sliders use accent-color: var(--ion).
  Row 2: Noise slider (50–1000, default 400) + RUN/STOP button (right-aligned).
  All sliders update simulation without stopping.

ADC PANEL (float animation 1):
  Left half of a 2-col grid:
    - Large mono D value (color: plasma if safe, danger if D>T_HIGH, amber if D<T_LOW)
    - Vin in volts below
    - Horizontal gauge bar 0–4095, fill color matches D state.
      Amber tick at T_LOW position, danger tick at T_HIGH position.
    - Axis labels: 0, T_L (amber), T_H (danger), 4095

GPIO ALERT PANEL (float animation 2, right half):
  Three LED rows: SAFE / HIGH / LOW
    SAFE LED: plasma bloom when active
    HIGH LED: danger bloom when active
    LOW LED:  amber bloom when active
  Alert status text below: STANDBY / GPIO: SAFE / GPIO: HIGH ALERT !! / GPIO: LOW !!

ARM THUMB ASSEMBLY PANEL (float animation 3):
  Header: "ARM THUMB POLLING LOOP" (Orbitron) + live cycle count badge (ion blue)

  Show exactly these 13 lines (address, opcode, args, comment):
    0x0000  LDR  R1,[ADC_DR]      ; read sensor
    0x0002  LDR  R2,=T_HIGH       ; upper bound
    0x0004  CMP  R1,R2            ; set flags
    0x0006  BGT  ALERT_H          ; D>T_HIGH?
    0x0008  LDR  R3,=T_LOW        ; lower bound
    0x000A  CMP  R1,R3            ; set flags
    0x000C  BLT  ALERT_L          ; D<T_LOW?
    0x000E  MOV  R0,#0x00         ; safe val
    0x0010  STR  R0,[GPIO_OUT]    ; GPIO low
    0x0012  B    POLL_START       ; loop
    ─── divider ───
    ALERT:  MOV  R0,#0xFF         ; alert val
    0x001A  STR  R0,[GPIO_OUT]    ; GPIO high
    0x001C  B    POLL_START       ; loop

  Animation (async, 70ms per step, non-blocking, animBusy flag):
    Active line: box-shadow inset 2px 0 0 var(--ion), opcode color = ion
    Fired branch: box-shadow inset 2px 0 0 var(--plasma), opcode color = plasma
    Alert path:  box-shadow inset 2px 0 0 var(--danger), opcode color = danger
    Arrow "→" appears on active line's arrow span

  Safe path: animate lines 0→9 sequentially, count cycles, return 'safe'
  High alert: animate 0→3 (BGT fires), jump to ALERT→LC, return 'high'
  Low alert:  animate 0→6 (BLT fires), jump to ALERT→LC, return 'low'

SENSOR CHART (float animation 4):
  Real-time line chart, last 50 points, height 90px.
  Dataset 1: D values. Per-point color (plasma/danger/amber per threshold state).
             Border color also updates to match current state.
  Dataset 2: T_HIGH — dashed danger line
  Dataset 3: T_LOW  — dashed amber line
  No X axis. Y axis 0–4095, 4 ticks max.

STATS STRIP (4 cards):
  POLL CYCLES — live cycle count (10=safe path, 12=alert path)
  RTOS PATH   — static "120+" in danger color
  ALERTS      — cumulative count, increments on every alert state
  SAMPLES     — cumulative count, increments every tick

LIVE EQUATION PROOF STRIP (float animation 5):
  Title: "LIVE EQUATION PROOFS" (Orbitron, dim color)
  2×3 grid of proof cards. Each updates every simulation tick.
  Card border-left: ion normally, plasma if safe, danger if alert.

  Card 1 — EQ1: "D = (Vin/Vref)×(2ⁿ−1)"
    Show: "(Vin/3.3)×4095 = D" with actual numbers

  Card 2 — EQ2: "Res = Vref/2ⁿ"
    Show: "3.3/4096 = X mV/step"

  Card 3 — EQ5/6: "Threshold check"
    Show: "D > T_HIGH → ALERT" or "D < T_LOW → ALERT" or "T_LOW ≤ D ≤ T_HIGH → SAFE"
    Card border: danger if alert, plasma if safe

  Card 4 — EQ8: "T_exec = N × T_clock"
    Show: "N × T_clk_ns = result ns @ coreMHz"
    Uses ACTIVE CORE's clock frequency

  Card 5 — EQ9: "T_latency = T_s + T_cmp + T_br"
    Show: "T_exec + 2ns = total ns"

  Card 6 — EQ12: "U = T_active / T_total"
    Show: "U = X.XXXXXX%"
    Uses active core's clock

════════════════════════════════════════════════
RIGHT COLUMN — LIVE RESEARCH GRAPHS
════════════════════════════════════════════════

Five chart panels, each with float animation and a live-dot indicator in the header.

GRAPH A — "IRQ ENTRY — CLOCK CYCLES"
  Bar chart. X: [M0, M0+, M3, M4]. Y: [16, 15, 12, 12]. Y range 10–18.
  Selected core bar = full color opacity. Others = 20% opacity (alpha version).
  Header shows: "[ CORTEX-M3 SELECTED ]" label in core color (updates on switch).
  Smooth animation on color change (Chart.js animation duration 500ms).

GRAPH B — "IRQ ENTRY — NANOSECONDS"
  Bar chart. X: same cores. Y: [500.0, 312.5, 166.7, 71.4]. Y suffix " ns".
  Same opacity rule as Graph A — selected = full, others = 20%.

GRAPH C — "CLOCK CYCLES PER RESPONSE PATH"
  Bar chart. 5 bars:
    Bar 0: "Poll\n(Nc @ XMHz\n=Yns)"  — value = pollCycles (live from simulation)
    Bar 1: "HW IRQ\nEntry (12c)"       — value = 12 (static)
    Bar 2: "ISR Context\nSave (8c)"    — value = 8 (static)
    Bar 3: "OS Sched\nOverhead"        — value = 100 (static)
    Bar 4: "Total RTOS\nPath"          — value = 120 (static)
  Colors: plasma, ion, amber, danger, #a31f2d
  Bar 0 label recalculates ns on BOTH: core switch AND every simulation tick.
    Formula: pollCycles × (1/activeCoreClockMHz × 1000) = ns
  Update with chart.update('active') for smooth animation.

GRAPH D — "RELATIVE MEMORY FOOTPRINT"
  Bar chart. X: [Standard OS, Lean RTOS, Bare-Metal ASM].
  Y: [100, 1.0, 0.5]. Y ticks: X% format.
  Colors: danger, amber, plasma. Static — does not change per core.
  Height: 100px canvas wrapper.

GRAPH E — "LIVE T_EXEC COMPARISON — all cores"
  Bar chart. X: [M0, M0+, M3, M4].
  Y: for each core k, T_exec = pollCycles × (1/(clk[k] × 1e6)) × 1e9
  Y suffix " ns".
  Same opacity rule as A and B (selected = full, others = 20%).
  Updates on BOTH: core switch AND every simulation tick (pollCycles changes).
  This is the KEY proof chart — same poll cycles, different ns across cores.

════════════════════════════════════════════════
CORE DATA — hard-code exactly
════════════════════════════════════════════════

const CORES = {
  m0:  { name:'M0',  full:'Cortex-M0',  cycles:16, clk:32,  ns:500.0, color:'#ff3b5c', alpha:'rgba(255,59,92,0.2)'  },
  m0p: { name:'M0+', full:'Cortex-M0+', cycles:15, clk:48,  ns:312.5, color:'#ffaa00', alpha:'rgba(255,170,0,0.2)'  },
  m3:  { name:'M3',  full:'Cortex-M3',  cycles:12, clk:72,  ns:166.7, color:'#00d4ff', alpha:'rgba(0,212,255,0.2)'  },
  m4:  { name:'M4',  full:'Cortex-M4',  cycles:12, clk:168, ns:71.4,  color:'#00ff9f', alpha:'rgba(0,255,159,0.2)'  }
};

════════════════════════════════════════════════
SIMULATION ENGINE
════════════════════════════════════════════════

Tick interval: 500ms via setInterval.

Each tick:
  sBase += direction × random(20, 100)
  if sBase > 4095 - noise: direction = -1
  if sBase < noise: direction = 1
  D = clamp(round(sBase + random(-noise, +noise)), 0, 4095)
  Vin = (D / 4095) × 3.3

Animation: async/await with setTimeout promises (70ms delay per ASM line).
animBusy flag prevents overlapping animations.
pollCycles = 10 for safe path, 12 for alert path.
alerts and samples are cumulative integers for the session.

Core switch (selCore function):
  1. Update active tab + core info bar highlight
  2. Rebuild Graph A colors (coreColors function)
  3. Rebuild Graph B colors
  4. Rebuild Graph C first bar label with new core ns
  5. Rebuild Graph E data for all 4 cores
  6. Update live-dot colors in graph headers
  7. Update proof strip EQ8/EQ9/EQ12 if simulation is running

updateGC() recalculates Graph C bar 0:
  pollCycles × (1 / (activeCoreClk × 1e6)) × 1e9 → toFixed(1) ns
  Label: "Poll\n("+pollCycles+"c @ "+clk+"MHz\n="+ns+"ns)"

updateGE() recalculates Graph E all bars:
  CKEYS.map(k => pollCycles × (1 / (CORES[k].clk × 1e6)) × 1e9)

════════════════════════════════════════════════
TECHNICAL CONSTRAINTS
════════════════════════════════════════════════

- Single HTML file. DOCTYPE, html, head, body all present. Works by double-click in Chrome.
- All CSS in <style> in <head>. All JS at bottom of <body>.
- Chart.js: load UMD from https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js
  Follow with plain <script> (NOT type="module") for all chart code.
- Canvas sizing: wrap every <canvas> in <div style="position:relative; height:Xpx">
  Use responsive:true, maintainAspectRatio:false. NEVER set height on canvas element.
- Float animations: use transform:translateY only. No top/margin changes (causes reflow).
- No position:fixed anywhere.
- No localStorage. All state in JS variables.
- No gradients, blur, or glow on CHART datasets — hardcoded hex only (Canvas ignores CSS vars).
- Round all displayed numbers: D=integer, Vin=.toFixed(3), ns=.toFixed(1), %=.toFixed(6)
- Multiple charts: unique canvas IDs. Each gets its own wrapper div.
- Chart.js legend: disable default (plugins:{legend:{display:false}}) and build none
  (the core info bar serves as the legend).
- chart.update('active') for animated updates, chart.update('none') for the real-time
  sensor line chart (performance).
- Google Fonts: load via @import url(...) at top of <style> block.
- backdrop-filter: include both -webkit-backdrop-filter and backdrop-filter for compatibility.

════════════════════════════════════════════════
OUTPUT REQUIREMENT
════════════════════════════════════════════════

Output ONE complete HTML file. Start with <!DOCTYPE html>. End with </html>.
The file must render correctly when saved and opened by double-clicking in Chrome.
Do not split into multiple files. Do not use any npm packages or build steps.
```

---

## Equation Verification Table

When checking the agent's output, verify these computed values match:

| Equation | Inputs | Expected |
|----------|--------|----------|
| EQ1 | Vin=1.65, Vref=3.3, n=12 | D = 2047 |
| EQ2 | Vref=3.3, n=12 | 0.806 mV/step |
| EQ3 | Ts=500ms | fs = 2 Hz |
| EQ5 | D=3500, T_HIGH=3200 | ALERT HIGH |
| EQ6 | D=500, T_LOW=800 | ALERT LOW |
| EQ8 (M3) | N=10, clk=72MHz | T_exec = 138.9 ns |
| EQ8 (M4) | N=10, clk=168MHz | T_exec = 59.5 ns |
| EQ8 (M0) | N=10, clk=32MHz | T_exec = 312.5 ns |
| EQ9 | T_exec=138.9, T_GPIO=2 | T_latency = 140.9 ns |
| EQ12 (M3) | N=10, clk=72MHz, Ts=0.5s | U = 0.000278% |

Graph C — verify bar 0 label:
- M0  selected, poll=10: label shows "10c @ 32MHz = 312.5ns"
- M3  selected, poll=10: label shows "10c @ 72MHz = 138.9ns"
- M4  selected, poll=12: label shows "12c @ 168MHz = 71.4ns"

Graph E — verify T_exec values (poll=10 cycles):
- M0:  10 × (1/32e6)  × 1e9 = 312.50 ns
- M0+: 10 × (1/48e6)  × 1e9 = 208.33 ns
- M3:  10 × (1/72e6)  × 1e9 = 138.89 ns
- M4:  10 × (1/168e6) × 1e9 =  59.52 ns

---

## Research Paper Context

**Title:** Sensor Data Acquisition and Threshold Alert System Using ARM Assembly
**Authors:** Hamza Rizvi, Samuel Okegbile
**Course:** Intro to Microprocessors
**Date:** February 10, 2026

Key findings the simulation must demonstrate:
1. Bare-metal polling uses 3 cycles (CMP + BGT/BLT) vs 120+ for RTOS
2. Cortex-M3/M4 achieve 12-cycle IRQ entry; M0 takes 16 cycles
3. M4 at 168MHz gives lowest latency (71.4ns) despite same cycle count as M3
4. Bare-metal has ~0.5% memory footprint vs 100% for full OS
5. T_exec varies dramatically across cores even for identical poll cycle counts
6. CPU utilization U is precisely controllable — under 0.001% at 500ms tick

---

## Alternative Theme Variants

Replace the AESTHETIC DIRECTION block with one of these:

### Clean Scientific (journal figure style)
```
White background #ffffff. Single accent #0052cc. Helvetica Neue or system-ui.
No animations except chart transitions. 1px solid #e0e0e0 borders.
All data in #0052cc. Labels in #666666. Charts use minimal 0.5px grid lines.
Think Nature journal supplementary figure. No glow, no blur, no float.
```

### Industrial CRT Terminal
```
Background #0a0a00. Phosphor green #33ff33 for all text and values.
Scan-line overlay at 10% opacity. text-shadow: 0 0 4px #33ff33 on all text.
No color variation — only green and black. Amber #ffcc00 for alerts only.
Monospace everything (Courier New fallback). Blink animation on alert state.
Charts: green bars on black. Grid lines at rgba(51,255,51,0.15).
```

### Glassmorphism Light
```
Background #f0f4ff. White panels with rgba(255,255,255,0.7) and blur(20px).
Accent #6366f1 (indigo). Success #10b981. Warning #f59e0b. Danger #ef4444.
Soft box-shadows: 0 8px 32px rgba(99,102,241,0.12). border-radius 16px.
Inter or DM Sans font. Subtle float animations. No scan lines.
```
