# UrSafe Real Location & Geographic Mapping Architecture

## 1. Principles of Real Location

UrSafe enforces strict geographic realism:
- **GPS Coordinates are the Source of Truth**: Coordinates (`latitude`, `longitude`, `accuracy_m`) are captured directly from hardware GNSS receivers.
- **No Mock or Landmark Coordinates**: System coordinates are never fabricated, rounded to generic city centers, or substituted with nearest landmark approximations.
- **Human-Readable Addresses are Derived**: Physical street addresses are derived via structured reverse geocoding from exact coordinates.

---

## 2. Location Data Model

Every location fix in UrSafe records:

```json
{
  "latitude": 28.650805,
  "longitude": 77.230014,
  "accuracy_m": 8.0,
  "altitude_m": 218.0,
  "heading_deg": 142.5,
  "speed_mps": 0.0,
  "provider": "GPS",
  "source": "HARDWARE_GNSS",
  "timestamp": 1729898400000,
  "formatted_address": "Chandni Chowk, Old Delhi, Delhi 110006, India"
}
```

---

## 3. Reverse Geocoding

The system converts raw coordinates into structured address entities:
- `street`: Street name and landmark (e.g. `Chandni Chowk`)
- `locality`: Sub-district / sector (e.g. `Old Delhi`)
- `district`: Administrative district (e.g. `Central Delhi`)
- `city`: City (e.g. `Delhi`)
- `state`: State or Province (e.g. `Delhi`)
- `postal_code`: Postal code (e.g. `110006`)
- `country`: Country (e.g. `India`)

### Offline Fallback
When connectivity is unavailable:
1. Exact coordinates remain the primary display.
2. If a cached address is available for the sector, it is displayed with an offline tag.
3. Once network connectivity is restored, reverse geocoding resolves the address automatically.

---

## 4. Map UX & Entity Differentiation

The coordinator tactical map renders real WGS84 coordinates with clear visual hierarchy:

| Entity | Visual Representation | Details on Selection |
| :--- | :--- | :--- |
| **Current User ("YOU")** | Distinct Cyan/Blue pulsating dot with accuracy radius circle | Operator name, role, GPS accuracy, freshness indicator (`● LIVE`) |
| **Emergency Incidents** | Red critical circle markers (color-coded by urgency: Critical=Red, High=Orange) | Category, urgency, victims, exact coordinates, link to full case modal |
| **Assigned Responders** | Emerald circle markers | Medic unit, badge, specialization, last updated timestamp |
| **Connected BLE Devices** | Cyan markers | UrSafe node identity, RSSI dBm, battery level |
| **Hazard Zones** | Translucent red polygon with dashed borders | Sensor advection zones (e.g. Flash flood depth > 1.2m) |

---

## 5. Map Controls

- **My Location**: Centers viewport directly on current operator coordinates with zoom level 16.
- **Fit Incidents**: Automatically calculates geographic bounds encompassing all active incidents and adjusts camera zoom.
- **Center on Command**: Centers viewport on command center coordinates.
- **Toggle Hazards**: Toggles display of environmental sensor overlay layers.
