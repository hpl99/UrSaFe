use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[repr(u8)]
pub enum Priority {
    Emergency = 1,
    High = 2,
    Routine = 3,
    Telemetry = 4,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MessageType {
    SosCreated,
    SosUpdated,
    SosCancelled,
    SosAcknowledged,
    SosAssigned,
    SosAccepted,
    SosDeclined,
    ResponderStatus,
    ResponderLocation,
    Arrived,
    RescueStarted,
    RescueCompleted,
    RescueReceipt,
    CredentialIssued,
    CredentialRevoked,
    RouteUpdate,
    NodeAnnouncement,
    HazardUpdate,
    SyncRequest,
    SyncResponse,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeliveryState {
    QueuedLocal,
    TransmittedMesh,
    Acknowledged,
    Delivered,
    Expired,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageEnvelope {
    pub message_id: String,
    pub sender_id: String,
    pub recipient_id: String,
    pub created_at: i64,
    pub expires_at: i64,
    pub priority: Priority,
    pub message_type: MessageType,
    pub sequence: u32,
    pub hop_limit: u8,
    pub origin: String,
    pub current_hop: String,
    pub payload: HashMap<String, serde_json::Value>,
    pub payload_hash: String,
    pub signature: String,
    pub delivery_state: DeliveryState,
}

impl MessageEnvelope {
    pub fn new(
        message_id: String,
        sender_id: String,
        recipient_id: String,
        created_at: i64,
        ttl_ms: i64,
        priority: Priority,
        message_type: MessageType,
        sequence: u32,
        hop_limit: u8,
        payload: HashMap<String, serde_json::Value>,
    ) -> Self {
        let payload_hash = Self::calculate_payload_hash(&payload);
        Self {
            message_id,
            origin: sender_id.clone(),
            current_hop: sender_id.clone(),
            sender_id,
            recipient_id,
            created_at,
            expires_at: created_at + ttl_ms,
            priority,
            message_type,
            sequence,
            hop_limit,
            payload,
            payload_hash,
            signature: String::new(),
            delivery_state: DeliveryState::QueuedLocal,
        }
    }

    pub fn calculate_payload_hash(payload: &HashMap<String, serde_json::Value>) -> String {
        let serialized = serde_json::to_string(payload).unwrap_or_default();
        let mut hasher = Sha256::new();
        hasher.update(serialized.as_bytes());
        hex::encode(hasher.finalize())
    }

    pub fn is_expired(&self, current_time_ms: i64) -> bool {
        current_time_ms >= self.expires_at
    }

    pub fn decrement_hop(&mut self, next_hop: &str) -> bool {
        if self.hop_limit <= 1 {
            self.hop_limit = 0;
            return false;
        }
        self.hop_limit -= 1;
        self.current_hop = next_hop.to_string();
        true
    }

    pub fn get_signing_bytes(&self) -> Vec<u8> {
        format!(
            "{}:{}:{}:{}:{}:{}:{:?}:{}:{}:{}",
            self.message_id,
            self.sender_id,
            self.recipient_id,
            self.created_at,
            self.expires_at,
            self.priority as u8,
            self.message_type,
            self.sequence,
            self.origin,
            self.payload_hash
        )
        .into_bytes()
    }
}
