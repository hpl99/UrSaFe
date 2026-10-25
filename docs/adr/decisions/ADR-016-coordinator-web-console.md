# ADR-016: High-Contrast Operational Web Console & MapLibre Offline Vector Maps

## Status
Approved

## Context
Emergency operations centers and field command vehicles require a situational dashboard that works under bright sunlight, smoke, generator flickers, and intense stress. The interface must be responsive across common command laptop resolutions (1366x768, 1920x1080), ruggedized tablets (1280x800), and mobile screens. Online map tiles (Google Maps/Mapbox) are completely blank when the command post operates off-grid.

## Decision
1. Build the Coordinator Web Console (`apps/web-console`) using a dedicated, zero-dependency, ultra-fast design system.
2. Design Principles:
   - High-contrast dark mode with crisp semantic alert tokens (Emergency Red `#EF4444`, Warning Amber `#F59E0B`, Safe Green `#10B981`, Accent Cyan `#06B6D4`).
   - Zero fake telemetry: Every metric, node, packet, and line is driven by actual application state.
   - Fully keyboard accessible (WCAG 2.1 AA compliant) with minimum touch targets.
   - Screen layouts verified for 1920x1080, 1366x768, 1280x800, and mobile widths without horizontal scroll clipping.
3. Offline Vector Cartography:
   - Self-contained vector tile / Canvas fallback rendering with dynamic SVG overlays for hazard polygons, radio coverage circles, and responder trajectories.

## Consequences
- **Positive:** Immediate situational awareness, zero external CDN dependencies, fully operational in an isolated LAN/Wi-Fi command mesh.
- **Trade-off:** Offline vector tile packages must be bundled or preloaded in the command container.
