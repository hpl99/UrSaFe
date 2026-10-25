"""
Domain Semantic Safety Guardrails
Enforces life-safety domain policy over raw CRDT mathematical state merges.
"""
from typing import Tuple, Dict, Any

# High-acuity on-scene states that must not be unilaterally aborted by remote cancellations
ON_SCENE_ACTIVE_STATES = {"ARRIVED", "RESCUE_STARTED", "RESCUE_IN_PROGRESS"}

class DomainSafetyGuard:
    @staticmethod
    def evaluate_transition(
        current_local_status: str,
        incoming_merged_status: str,
        current_assigned_responder: str,
        incoming_assigned_responder: str,
    ) -> Tuple[str, str, bool, str]:
        """
        Evaluates an incoming CRDT state merge against life-safety guardrails.
        Returns:
          (resolved_status, resolved_responder, conflict_flag, policy_rationale)
        """
        # Guardrail 1: Rescuer On-Scene Protection
        # If the local responder is already on-scene (ARRIVED / RESCUE_STARTED),
        # an incoming CANCELLED or REASSIGNED status from an isolated partition
        # must NOT force the on-scene rescuer to abort.
        if current_local_status in ON_SCENE_ACTIVE_STATES:
            if incoming_merged_status in ("CANCELLED", "REPORTED", "ASSIGNED"):
                return (
                    current_local_status,
                    current_assigned_responder,
                    True,
                    f"SAFETY OVERRIDE: Preserved on-scene state '{current_local_status}'. "
                    f"Blocked incoming remote cancellation '{incoming_merged_status}' pending coordinator review."
                )

        # Guardrail 2: Completed Rescue Protection
        # A rescue marked COMPLETED or RESCUED cannot be rolled back to in-progress or cancelled.
        if current_local_status in ("RESCUED", "RESCUE_COMPLETED"):
            if incoming_merged_status != current_local_status:
                return (
                    current_local_status,
                    current_assigned_responder,
                    True,
                    f"SAFETY OVERRIDE: Preserved verified rescue completion. "
                    f"Blocked incoming status '{incoming_merged_status}'."
                )

        # Normal CRDT convergence allowed
        return (
            incoming_merged_status,
            incoming_assigned_responder,
            False,
            "State converged normally under standard CRDT rules."
        )
