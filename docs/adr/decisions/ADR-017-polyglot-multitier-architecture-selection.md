# ADR-017: Polyglot Multi-Tier Architecture & Technology Selection

## Status
Approved

## Context
Emergency communication across disconnected disaster environments requires solving fundamentally diverse engineering problems that cannot be optimally addressed by a single programming language or runtime:
1. **Field Mobile Applications** require native Android OS hooks (Bluetooth LE Nordic UART service, USB serial, background execution without OS kill, Android Keystore hardware cryptography, native lock-screen notifications, Room SQLite).
2. **Core Protocol, Cryptography & CRDT State** require memory safety without garbage collection pauses, constant-time cryptographic primitives, strict zero-copy binary serialization, and zero-crash deterministic state machines.
3. **Web Coordinator Console** requires high-performance DOM/Canvas rendering, type-safe reactive state, and broad cross-platform responsiveness.
4. **AI/NLP Triage & Scientific Modeling** require vector math, rapid iteration, and statistical calibration tooling.

## Subsystem Classification & Decision Matrix

| Layer / Subsystem | Chosen Technology | Classification | Justification | Interface Boundaries |
| :--- | :--- | :--- | :--- | :--- |
| **1. Field Mobile (Victim & Responder)** | **Kotlin / Android (Native)** | **REWRITE / NATIVE** | Android OS handles low-level BLE/USB radio streams, Android Keystore, background foreground services, and Room persistence. Web PWAs or Python cannot sustain background BLE radios. | Interfaces with Rust core via JNI/Protobuf; communicates with Meshtastic radios via BLE NUS/USB serial. |
| **2. Core Cryptography, Protocol & CRDT** | **Rust (`ursafe-core-rs`)** | **REWRITE / INTEGRATE** | Eliminates entire classes of memory vulnerabilities (buffer overflows, use-after-free). Guarantees constant-time crypto execution, zero-copy protobuf parsing, and sub-millisecond CRDT joins. | Exposes C-ABI (`librsafe_core`), Protobuf wire definitions, and UniFFI / WASM bindings. |
| **3. Hardware Transport Abstraction** | **Kotlin (Mobile) & Rust/Python (Stationary/Node)** | **REFACTOR** | Hardware drivers for Meshtastic SX1262 LoRa, Nordic nRF52 BLE, and FTDI USB serial. Abstracted behind unified `Transport` interface. | `Transport` trait / interface emitting raw binary packets to the Core. |
| **4. Coordinator Web Application** | **TypeScript / HTML5 Canvas / Vanilla CSS** | **REWRITE / TS** | Zero-bundle-rot operational dashboard. Fast, reactive, responsive across 1920x1080 to mobile. MapLibre vector cartography. | Communicates via WebSocket & REST with API; can run standalone in offline local LAN. |
| **5. Central Backend & Control Plane** | **TypeScript / Node.js & Rust** | **REFACTOR / INTEGRATE** | High-concurrency asynchronous I/O, native JSON/Protobuf streaming, seamless TypeScript contract sharing with web console. | OpenAPI 3.0 REST + WebSocket JSON/Protobuf streams + PostgreSQL. |
| **6. AI / NLP / Hazard Modeling** | **Python (Scientific & Triage Engine)** | **KEEP / SPECIALIZED** | Optimal for character n-grams, multilingual phonetic normalization (Hindi/Hinglish), kinematic polygon evaluation, and probability calibration (Brier, ECE). | Standalone micro-engine / CLI tool callable via standard IPC or embedded in node runtimes. |
| **7. Simulation & Red-Team Test Suite** | **Python & Shell / Rust Harness** | **KEEP / EXPAND** | Monte Carlo CRDT fuzzing, multi-node partition simulation, red-team packet replay, and automated regression testing. | In-memory loopback and network pipe harnesses. |

## Detailed Justification by Language

### Why Kotlin for Mobile?
- **Hardware Integration:** Android is the dominant operating system in disaster-prone regions worldwide. Direct access to `android.bluetooth.le`, `android.hardware.usb`, and `androidx.security.crypto.MasterKeys`.
- **Background Execution:** Android 14+ aggressively kills background processes. Only native Android `ForegroundService` with notification channels can maintain persistent BLE connections to Meshtastic radios when the screen is locked.
- **Local Persistence:** Android Room provides compile-time verified SQL queries with SQLCipher encryption.

### Why Rust for Core Protocol & Cryptography?
- **Security:** Memory safety without garbage collection stops buffer overflow exploits in packet decoders.
- **Performance:** Constant-time cryptographic execution protects against timing attacks.
- **Portability:** Compiles to static C-ABI libraries for Android JNI, native binaries for Linux/Windows gateway routers, and WebAssembly for browser verification.

### Why TypeScript for Web Console & Coordination API?
- **Shared Types:** Eliminates mismatch between coordinator console state and API endpoints through shared TypeScript interfaces derived from Protobuf and OpenAPI schemas.
- **Asynchronous Concurrency:** Node.js event-loop excels at thousands of concurrent WebSocket connections from field radios and data mules.
- **Accessibility & Rendering:** Direct DOM and Canvas rendering for high-contrast tactical maps without heavy bloated framework overhead.

### Why Python for NLP & Scientific Modeling?
- **Algorithmic Ergonomics:** Matrix math, polygon geometry, and linguistic n-gram tokenization are expressed cleanly with minimal boilerplate.
- **Calibration Verification:** Computing Expected Calibration Error (ECE) and reliability diagrams with scientific libraries.

## Consequences
- **Boundary Management:** Requires disciplined contracts (`contracts/messages.proto` and `contracts/openapi.yaml`) to ensure seamless interop across Kotlin, Rust, TypeScript, and Python.
- **Tooling:** Developers have clear, isolated modules: `apps/` for applications, `packages/` for shared libraries, `services/` for domain engines, and `hardware/` for radio adapters.
