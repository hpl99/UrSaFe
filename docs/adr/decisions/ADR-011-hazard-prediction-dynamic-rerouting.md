# ADR-011: Time-Aware Hazard Prediction & Dynamic Responder Rerouting

## Status
Approved

## Context
Dispatching emergency units based solely on static distance or road networks is dangerous during disasters. An advancing flood wave, moving wildfire flank, or secondary landslide can trap responders on their route. Dispatch engines that evaluate only current hazard conditions ($t=t_0$) fail when the responder reaches the danger area at $t = t_0 + \text{ETA}$.

## Decision
1. Implement a Time-Aware Hazard Engine:
   - Hazards are modeled as spatial polygons with severity, validity intervals, and kinematic growth models (rate and direction vectors).
   - The engine explicitly distinguishes `OBSERVED`, `PREDICTED`, and `REPORTED` hazard boundaries.
2. Calculate **Hazard at Arrival**:
   $$\text{PredictedHazard}(t_0 + \text{ETA}) = \text{Polygon}(t_0) \oplus (\vec{v}_{\text{growth}} \cdot \text{ETA})$$
3. When evaluating responder dispatch routes:
   - If intersection between route and predicted hazard polygon occurs, the engine:
     1. Automatically computes a hazard-avoiding perimeter reroute.
     2. If no safe route exists, flags `HOLD_AT_SAFE_PERIMETER`.
     3. Notifies both responder and incident coordinator with explanatory rationale.
   - Responders and coordinators always maintain manual human override capability.

## Consequences
- **Positive:** Protects responder lives and prevents resource stranding.
- **Trade-off:** Hazard progression models require parameter calibration based on terrain and weather reports.
