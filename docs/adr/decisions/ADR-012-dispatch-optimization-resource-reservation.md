# ADR-012: Deterministic Multi-Criteria Dispatch & Scarce Resource Reservation

## Status
Approved

## Context
Standard dispatch systems apply naive greedy heuristics (assigning the nearest available unit to the oldest call). Under mass-casualty conditions with scarce specialized resources (e.g. only one advanced cardiac life support medic or heavy rescue crane), greedy allocation rapidly exhausts critical assets on non-critical cases, leading to unserved life-threatening emergencies.

## Decision
1. Implement a deterministic multi-criteria dispatch optimization engine:
   - Evaluates severity weight ($W_{\text{sev}}$), arrival latency ($T_{\text{arr}}$), responder skill match ($M_{\text{skill}}$), hazard exposure ($H_{\text{exp}}$), and fairness.
2. Implement **Scarce Resource Reservation**:
   - If specialized units are scarce and critical incidents exist or are highly probable based on verified risk reports, specialized units are reserved for high-acuity life threats rather than routine triage.
   - *Conservative Policy*: A verified life-threatening emergency is never delayed for speculative future demand.
3. Automated benchmark comparing greedy vs. optimized dispatch on identical deterministic seeds to measure empirical arrival times, critical case latency, and unserved rates.

## Consequences
- **Positive:** Empirically reduces critical incident delay and prevents misallocation of life-saving specialists.
- **Trade-off:** Slightly higher computational complexity ($O(N \cdot M)$) than naive nearest-neighbor ($O(1)$).
