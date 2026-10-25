# UrSafe Geospatial Mapping & GNSS Specification

## 1. Real Geographic Coordinates vs. Simulated Grid

A critical design requirement (Section 15, 22) is the complete elimination of artificial game-like visual grids. All UrSafe operational interfaces render on **real-world geographic maps** using standard WGS84 coordinates (`Latitude`, `Longitude`, `Altitude MSL`).

| Interface | Map Technology | Primary Layer | Offline Capability |
|---|---|---|---|
| **Authority Command Console** | Leaflet 1.9.4 | OpenStreetMap Tile Layer | Browser Cache + Offline Vector Fallback |
| **Android Field Apps** | Google Maps SDK for Android | Vector Map Tiles | Local MBTiles SQLite Cache |

---

## 2. Real-Time Hardware GNSS & "Where Am I?" (Section 24)

Location is acquired directly from physical hardware sensors:
- **Web Console**: `navigator.geolocation.watchPosition` with `enableHighAccuracy: true`.
- **Android Apps**: Android `FusedLocationProviderClient` with `PRIORITY_HIGH_ACCURACY`.

### Coordinate Integrity Contract:
- **No Fabricated Locations**: If the device does not have a GNSS fix or permissions are denied, the UI explicitly shows:
  ```text
  LOCATION UNAVAILABLE
  Enable location permissions and ensure a clear view of the sky.
  ```
- **Accuracy Radius**: Every displayed position includes uncertainty radius (e.g., `±4.2 meters`).
- **Timestamp**: Fixes display the exact hardware epoch time.

---

## 3. Map Layers & Operational Overlays

1. **User Location**: Cyan circle marker with accuracy halo (`YOU ARE HERE`).
2. **Emergency Incidents**:
   - `CRITICAL` (Red `#FF334B`, 11px radius)
   - `HIGH` (Orange `#FF9100`, 9px radius)
   - `MEDIUM / LOW` (Blue `#2979FF`, 7px radius)
3. **Hazard Polygons**: Real-time sensor-driven geofences (e.g. Milan Subway flash flood advection zone with semi-transparent red fill and dashed boundary).
4. **Responder Location & Routes**: Displays responder vehicles and calculated shortest evacuation corridors.

---

## 4. Offline Map Strategy

In deep blackout zones with zero cellular or internet access:
- **Pre-cached Vector Tiles**: Regional disaster management authorities load 50MB MBTiles packages for active operational sectors (e.g., Greater Mumbai, Uttarkashi, Wayanad).
- **Lightweight SVG Vector Fallback**: When raster tile loading fails, Leaflet switches gracefully to localized GeoJSON street vector lines.
