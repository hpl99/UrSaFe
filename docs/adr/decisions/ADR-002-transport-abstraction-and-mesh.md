# ADR-002: Multi-Bearer Transport Abstraction & Meshtastic LoRa Integration

## Status
Approved

## Context
Emergency field responders utilize heterogeneous communications hardware: Meshtastic LoRa radios (Heltec V3, T-Beam) connected via BLE or USB, point-to-point BLE between smartphones, ad-hoc Wi-Fi Direct, and stationary gateway relays. Hardcoding the system to a single radio API creates tight vendor coupling and prevents automated testing in headless CI environments.

## Decision
1. Introduce a hardware-agnostic `Transport` interface defining `discover()`, `connect()`, `disconnect()`, `send()`, `receive()`, `getCapabilities()`, and `getLinkMetrics()`.
2. Implement `MeshtasticTransport` wrapping Meshtastic's Protocol Buffer stream protocol over BLE Nordic UART Service (NUS) and USB serial.
3. Implement `BleTransport` for direct peer-to-peer smartphone discovery and exchange.
4. Implement `SimulationTransport` for multi-node in-memory testing with simulated packet loss, latency, radio range, and partitions.
5. All upper layers (Outbox, Router, Sync Engine) interact exclusively with the `Transport` interface.

## Consequences
- **Positive:** Modular architecture; enables physical Meshtastic operation in the field while guaranteeing 100% deterministic testability in CI.
- **Trade-off:** Adapters must translate packet MTU limitations (e.g. 237 bytes on LoRa) and handle link-level fragmentation.
