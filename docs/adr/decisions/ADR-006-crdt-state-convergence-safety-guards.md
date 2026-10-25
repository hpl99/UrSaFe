# ADR-006: CRDT State Convergence & Domain Semantic Safety Guardrails

## Status
Approved

## Context
Concurrent mutations across network partitions will inevitably lead to conflicting incident states (e.g. Responder A accepts Incident 1 on Island Alpha, while Coordinator B assigns Incident 1 on Island Beta; or Cloud cancels an incident while Responder in the field is already executing rescue). Relational transactions fail without connectivity, and pure timestamp LWW (Last-Write-Wins) silently overwrites critical life-safety updates due to clock drift.

## Decision
1. Implement state-based Conflict-Free Replicated Data Types (CRDTs):
   - **Vector Clocks** to track causal precedence across nodes.
   - **LWW-Element-Set & ORSet** for incident status and responder assignment collections.
   - Mathematical idempotence, commutativity, and associativity on merge operations.
2. Implement **Domain Semantic Safety Guardrails**:
   - CRDT convergence handles state synchronization, but emergency domain rules supersede pure clock timestamps.
   - *Rule*: If a field responder has marked `ARRIVED` or `RESCUE_STARTED`, an older or concurrent remote `ASSIGNMENT_CANCELLED` operation will NOT abort the on-scene operation. The conflict is flagged for human coordinator review while keeping the rescuer and victim safe.

## Consequences
- **Positive:** Deterministic convergence across all islands without split-brain crashes or data loss.
- **Trade-off:** State representations require metadata tracking (vector clocks, tombstone cleanup).
