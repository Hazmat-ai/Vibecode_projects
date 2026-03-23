# ARM Cortex-M Sensor Threshold Alert Simulator

**Course:** Intro to Microprocessors  
**Authors:** Hamza Rizvi & Samuel Okegbile  
**Date:** February 2026  
**Assignment:** Sensor Data Acquisition and Threshold Alert System Using ARM Assembly

---

## Overview

This project is an interactive, browser-based simulation of a **bare-metal ARM assembly
sensor data acquisition and threshold alert system**. It visually proves all 12 equations,
all 5 research graphs, and the ARM Thumb polling loop — side by side, in real time — with
every graph updating live as you switch between Cortex cores.

The simulator runs as a single `.html` file in Chrome. No server, no build tools, no install
required. Chart.js is loaded via CDN (internet needed for graphs), or can be inlined for
fully offline use.

---

## How to Run

1. Open `arm_simulator.html` in Chrome (double-click the file)
2. Select a Cortex core from the top bar: **M0 / M0+ / M3 / M4**
3. Hit **RUN**
4. Adjust T_LOW, T_HIGH, and Noise sliders while running
5. Watch all 5 graphs and the equation proof strip update live

To make fully offline: paste the HTML into a new Claude chat and say
"inline the Chart.js 4.4.1 source directly into a script tag so this works with no internet."

---

## Layout

The screen is split into two live-linked columns:

**Left — Live Simulation**
- Generates live 12-bit ADC readings: `D = (Vin/Vref) × (2ⁿ − 1)`
- Animates all 13 ARM Thumb instructions with glow effects, line by line
- GPIO alert LEDs (SAFE / HIGH / LOW) pulse when thresholds are breached
- Live sensor trace chart with T_HIGH and T_LOW threshold lines
- Live Equation Proof strip — 6 equations evaluated with real numbers every sample

**Right — Live Research Graphs**
- All 5 graphs update the moment you switch Cortex cores
- Graph C first bar (poll cycles) updates every simulation tick
- Graph E (T_exec comparison) recalculates across all four cores simultaneously

---

## The 5 Live Graphs

| Graph | Title | What Changes Per Core |
|-------|-------|-----------------------|
| A | IRQ Entry Latency — Clock Cycles | Selected bar full brightness, others fade |
| B | IRQ Entry Latency — Nanoseconds | Selected bar full brightness, others fade |
| C | Clock Cycles Per Response Path | First bar label shows actual ns for active core |
| D | Relative Memory Footprint | Static reference (same across all cores) |
| E | Live T_exec Comparison | All 4 bars recalculate using live poll cycle count |

---

## The 12 Equations

| # | Name | Formula | Proved Live |
|---|------|---------|-------------|
| EQ1 | ADC Digital Output | `D = (Vin/Vref) × (2ⁿ − 1)` | Yes — proof strip |
| EQ2 | ADC Resolution | `Res = Vref / 2ⁿ` | Yes — proof strip |
| EQ3 | Sampling Frequency | `fs = 1 / Ts` | Yes — 2 Hz tick |
| EQ4 | Nyquist Condition | `fs ≥ 2 × fmax` | Yes — proof strip |
| EQ5 | Upper Threshold | `D > T_HIGH → alert` | Yes — proof strip goes red |
| EQ6 | Lower Threshold | `D < T_LOW → alert` | Yes — proof strip goes amber |
| EQ7 | Safe Operating Condition | `T_LOW ≤ D ≤ T_HIGH` | Yes — proof strip goes green |
| EQ8 | CPU Execution Time | `T_exec = N × T_clock` | Yes — recalculates per core |
| EQ9 | Polling Loop Latency | `T_latency = T_s + T_cmp + T_br` | Yes — updates per cycle count |
| EQ10 | GPIO Activation Time | `T_alert = T_exec + T_GPIO` | Yes — proof strip |
| EQ11 | Power Consumption | `P = V × I` | Yes — proof strip |
| EQ12 | CPU Utilization | `U = T_active / T_total` | Yes — updates per core |

---

## Core Data

| Core | IRQ Cycles | Max Clock | Latency | ISA | T_clock |
|------|-----------|-----------|---------|-----|---------|
| Cortex-M0 | 16 | 32 MHz | 500.0 ns | ARMv6-M | 31.25 ns |
| Cortex-M0+ | 15 | 48 MHz | 312.5 ns | ARMv6-M | 20.83 ns |
| Cortex-M3 | 12 | 72 MHz | 166.7 ns | ARMv7-M | 13.89 ns |
| Cortex-M4 | 12 | 168 MHz | 71.4 ns | ARMv7-ME | 5.95 ns |

Bare-metal polling path: **3 cycles** (CMP + branch) on every core.
RTOS interrupt path: **120+ cycles** (12 HW + 8 context save + ~100 OS scheduler).

---

## File Structure

```
arm_simulator.html    — open this in Chrome to run the simulator
README.md             — this file
AGENT_CONTEXT.md      — full agent prompt to regenerate in any theme/style
```

---

## Demo Script — March 26

**Before class:** Open `arm_simulator.html` in Chrome. Select M3. Set T_LOW=800, T_HIGH=3200, Noise=400.

1. **Introduce** — "Left is the live simulation, right is the graphs from our paper proving it"
2. **Hit RUN** — let it run safe ~10 seconds. Point to Graph A: M3 highlighted at 12 cycles
3. **Show EQ1** — proof strip: "(Vin/3.3)×4095 = D — the exact equation from page 5, live"
4. **Trigger HIGH alert** — drag T_LOW up past 2000. LED fires. Point to Graph C first bar jumping
5. **Switch to M0** — Graphs A and B bars shift. Graph E recalculates. EQ8 updates ns value
6. **Switch to M4** — "Same 12 interrupt cycles as M3 but 168 MHz clock = 71.4 ns latency"
7. **Point to Graph D** — "Bare-metal uses 0.5% memory vs 100% for a full OS"
8. **Wrap** — "Every graph, every equation in the paper is running live right here"

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Charts blank | Needs internet for Chart.js CDN — ask Claude to inline it |
| No animation | Enable JavaScript in Chrome settings |
| Graphs not updating on core switch | Refresh the page |
| File won't open | Right-click → Open with → Google Chrome |
