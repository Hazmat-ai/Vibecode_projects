# Signal Bench model

## Signal and threshold rules

The default signal is a sine centered at 2047.5 codes, amplitude 1700 codes, with uniform seeded noise. Values are rounded and clamped to the 12-bit range 0–4095. The LCG seed makes a reset repeatable for unchanged settings and controls. Manual mode supplies an exact integer code. Simulated time accumulates using each sample's configured interval, so changing the sample rate does not move time backwards.

`D < T_LOW` is low, `D > T_HIGH` is high, and both endpoints are safe. GPIO values 0, 1, and 2 are illustrative safe/high/low states. No memory-mapped registers, real pins, firmware, DMA, interrupts, or ADC hardware are executed.

The display uses the rounded ideal code map `D = round((Vin/Vref) × (2ⁿ−1))` and its inverse for voltage. It separately reports the ideal quantization-bin width `Vref/2ⁿ`. This does not reproduce a specific ADC's transfer function, acquisition time, reference errors, or effective resolution.

## Instruction paths and timing

The illustrative Thumb-like listing uses unsigned `BHI` / `BLO` comparisons and separate high/low labels. The engine selects only executed instructions:

| State | Instruction indices (zero-based) | Default modeled cycles |
| ----- | -------------------------------- | ---------------------- |
| Safe  | 0–9                              | 16                     |
| High  | 0–3, 10–12                       | 14                     |
| Low   | 0–6, 13–15                       | 18                     |

These totals are derived from **assumed** LDR=2, STR=2, taken branch=3, other instruction or untaken conditional branch=1. Loads of threshold literals and registers are conceptual; no assembler expansion or instruction encoding is verified. Costs are editable and are not promised to match any Cortex implementation. Flash waits, bus contention, ADC acquisition, pipeline specifics, and compiler/assembler decisions can change real execution time.

Execution time is the summed path cost divided by clock frequency. Read-to-GPIO time sums only the prefix through STR, then adds the assumed extra GPIO delay. The sampled detection bound adds one sample interval. It assumes that sampling occurs within that interval and that no other work delays the path; a browser timer does not supply a real-time guarantee.

The reported work fraction is per-sample modeled execution divided by sampling interval. **It is not total CPU utilization.** A continuously busy polling implementation may occupy the core between sample events.

## Core references

The reference exception-entry counts are M0=16, M0+=15, M3=12, M4=12, under ideal zero-wait-state conditions. They describe exception entry, not complete ISR handling or a universal RTOS response. See [Arm's interrupt latency guide](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/beginner-guide-on-interrupt-latency-and-interrupt-latency-of-the-arm-cortex-m-processors) and [Arm Cortex-M for Beginners](https://community.arm.com/cfs-file/__key/telligent-evolution-components-attachments/01-2057-00-00-00-01-28-35/Cortex_2D00_M-for-Beginners-_2D00_-2017_5F00_EN_5F00_v2.pdf).

32/48/72/168 MHz are example system settings, not core maximum specifications. Core comparisons hold the current modeled path costs constant while varying clock and exception-entry reference counts. This isolates the arithmetic; it is not a general performance ranking.

The Nyquist check applies only to the configured clean sine. Random noise has no band limit in this generator. The app displays `P = V × I` but does not invent a current value to claim a power result.

## Captures

Up to 1,000 samples are retained in memory; the plot shows the latest 60. CSV includes each sample's core, clock, thresholds, and sample rate so changed settings remain interpretable. Settings JSON contains a format version and validated configuration; it does not claim to preserve captured history or live hardware state. Reloading or resetting clears the capture. The app pauses when its tab becomes hidden.
