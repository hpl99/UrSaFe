pub mod protocol;
pub mod crypto;
pub mod crdt;

pub use protocol::{MessageEnvelope, Priority, MessageType, DeliveryState};
pub use crypto::{RustEd25519KeyPair, RustReplayFilter};
pub use crdt::{RustVectorClock, RustLWWRegister};

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_rust_protocol_envelope() {
        let mut payload = HashMap::new();
        payload.insert("status".to_string(), serde_json::json!("EMERGENCY"));

        let mut env = MessageEnvelope::new(
            "msg_01".to_string(),
            "node_alpha".to_string(),
            "BROADCAST".to_string(),
            1000,
            60000,
            Priority::Emergency,
            MessageType::SosCreated,
            1,
            5,
            payload,
        );

        assert_eq!(env.priority, Priority::Emergency);
        assert!(!env.is_expired(2000));
        assert!(env.is_expired(70000));

        let forwarded = env.decrement_hop("node_beta");
        assert!(forwarded);
        assert_eq!(env.hop_limit, 4);
        assert_eq!(env.current_hop, "node_beta");
    }

    #[test]
    fn test_rust_ed25519_sign_verify() {
        let kp = RustEd25519KeyPair::generate();
        let message = b"EMERGENCY_FIELD_SOS_COORDINATE";
        let sig = kp.sign(message);
        assert_eq!(sig.len(), 64);
        assert!(kp.verify(message, &sig));
        assert!(!kp.verify(b"TAMPERED", &sig));
    }

    #[test]
    fn test_rust_vector_clock_merge() {
        let mut v1 = RustVectorClock::new();
        v1.increment("node_a");

        let mut v2 = RustVectorClock::new();
        v2.increment("node_b");
        v2.increment("node_b");

        let merged = v1.merge(&v2);
        assert_eq!(merged.get("node_a"), 1);
        assert_eq!(merged.get("node_b"), 2);
    }
}
