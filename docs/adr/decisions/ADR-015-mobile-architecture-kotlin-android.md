# ADR-015: Native Android Mobile Architecture (Kotlin, Room, Coroutines)

## Status
Approved

## Context
Emergency field users require rock-solid background radio connectivity, low-latency BLE peripheral access, hardware keystore cryptography, and instant push notifications even when the device is locked or power-saving. Web PWAs in mobile browsers cannot reliably sustain background BLE connections, cannot access hardware secure enclaves reliably, and are terminated by Android's aggressive battery optimization.

## Decision
1. Standardize on native Android with Kotlin for mobile applications:
   - `apps/victim-android`: High-urgency, stress-resilient civilian distress application.
   - `apps/responder-android`: Tactical volunteer/responder operations application.
2. Architecture:
   - **UI Layer**: Jetpack Compose / ViewModels with immutable UI state.
   - **Domain Layer**: Clean Architecture use cases (`CreateEmergencyUseCase`, `AcceptAssignmentUseCase`, `SyncOutboxUseCase`).
   - **Data Layer**: Room SQLite with SQLCipher encryption, Coroutines & Flow for reactive state.
   - **Hardware Integration**: Android BluetoothLeScanner, Foreground Service for continuous radio connection, Android Keystore for Ed25519/X25519 keys.

## Consequences
- **Positive:** Uncompromised hardware access, deterministic background services, battery-efficient BLE operations.
- **Trade-off:** Requires maintaining native Android codebases; iOS support evaluated separately.
