use serde::{Deserialize, Serialize};
use std::cmp::max;
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RustVectorClock {
    pub clock: HashMap<String, u64>,
}

impl RustVectorClock {
    pub fn new() -> Self {
        Self {
            clock: HashMap::new(),
        }
    }

    pub fn increment(&mut self, node_id: &str) {
        let count = self.clock.entry(node_id.to_string()).or_insert(0);
        *count += 1;
    }

    pub fn get(&self, node_id: &str) -> u64 {
        *self.clock.get(node_id).unwrap_or(&0)
    }

    pub fn merge(&self, other: &RustVectorClock) -> RustVectorClock {
        let mut merged = self.clock.clone();
        for (node, &other_val) in &other.clock {
            let entry = merged.entry(node.clone()).or_insert(0);
            *entry = max(*entry, other_val);
        }
        RustVectorClock { clock: merged }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RustLWWRegister<T: Clone + PartialEq + Eq> {
    pub value: T,
    pub timestamp: i64,
    pub node_id: String,
}

impl<T: Clone + PartialEq + Eq> RustLWWRegister<T> {
    pub fn new(value: T, timestamp: i64, node_id: String) -> Self {
        Self {
            value,
            timestamp,
            node_id,
        }
    }

    pub fn merge(&self, other: &RustLWWRegister<T>) -> RustLWWRegister<T> {
        if self.timestamp > other.timestamp {
            self.clone()
        } else if other.timestamp > self.timestamp {
            other.clone()
        } else if self.node_id >= other.node_id {
            self.clone()
        } else {
            other.clone()
        }
    }
}
