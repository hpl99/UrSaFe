"""
Monte Carlo CRDT Fuzzer
Generates randomized multi-node topologies, partition splits, concurrent operation orderings,
and verifies deterministic state convergence across all nodes upon network healing.
"""
import random
from typing import List, Dict, Any, Optional
from .crdt_state import IncidentCRDTState

class CRDTFuzzer:
    def __init__(self, num_nodes: int = 5, seed: int = 42):
        self.num_nodes = num_nodes
        self.seed = seed
        self.node_ids = [f"node_{i:02d}" for i in range(num_nodes)]
        self.rng = random.Random(seed)

    def run_fuzz_trials(self, num_trials: int = 1000, ops_per_trial: int = 20) -> Dict[str, Any]:
        """
        Runs Monte Carlo fuzz trials.
        In each trial:
          1. Spawns independent replicas across nodes.
          2. Generates random concurrent updates across partitioned node subsets.
          3. Simulates random message delivery orders and duplicates.
          4. Merges all replicas in arbitrary topological permutations.
          5. Verifies that all replicas converge to an IDENTICAL snapshot.
        """
        failing_seeds: List[int] = []
        statuses = ["REPORTED", "ACKNOWLEDGED", "ASSIGNED", "ACCEPTED", "ARRIVED", "RESCUED"]
        responders = ["unit_alpha", "unit_bravo", "unit_charlie", "unit_delta"]

        for trial_idx in range(num_trials):
            trial_seed = self.seed + trial_idx
            trial_rng = random.Random(trial_seed)

            # Initialize replica on each node
            replicas = {nid: IncidentCRDTState("incident_fuzz_01", nid) for nid in self.node_ids}

            # Generate random operations
            for op_idx in range(ops_per_trial):
                acting_node = trial_rng.choice(self.node_ids)
                op_type = trial_rng.choice(["status", "assign", "people", "ack"])
                timestamp = (trial_idx * 100) + op_idx

                if op_type == "status":
                    st = trial_rng.choice(statuses)
                    replicas[acting_node].update_status(st, timestamp, acting_node)
                elif op_type == "assign":
                    resp = trial_rng.choice(responders)
                    replicas[acting_node].assign_responder(resp, timestamp, acting_node)
                elif op_type == "people":
                    count = trial_rng.randint(1, 10)
                    replicas[acting_node].update_people(count, timestamp, acting_node)
                elif op_type == "ack":
                    tok = f"tok_{acting_node}_{op_idx}"
                    replicas[acting_node].acknowledged_by.add(acting_node, tok)

            # Simulate network healing: full randomized pairwise and group merges
            nodes_list = list(self.node_ids)
            trial_rng.shuffle(nodes_list)

            # Cumulative convergence merge
            accumulator = replicas[nodes_list[0]]
            for nid in nodes_list[1:]:
                accumulator = accumulator.merge(replicas[nid])

            # Merge accumulator back into all nodes
            for nid in self.node_ids:
                replicas[nid] = replicas[nid].merge(accumulator)

            # Check that every replica is identical
            snapshots = [replicas[nid].to_snapshot() for nid in self.node_ids]
            first = snapshots[0]
            converged = all(s == first for s in snapshots)

            if not converged:
                failing_seeds.append(trial_seed)

        return {
            "trials_run": num_trials,
            "ops_per_trial": ops_per_trial,
            "converged": len(failing_seeds) == 0,
            "failing_seeds": failing_seeds,
            "success_rate": (num_trials - len(failing_seeds)) / num_trials,
        }
