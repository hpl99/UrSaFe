use std::collections::{HashMap, HashSet};
use ed25519_dalek::{Signer, SigningKey, Verifier, VerifyingKey, Signature};

pub struct RustEd25519KeyPair {
    pub signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
}

use rand::RngCore;

impl RustEd25519KeyPair {
    pub fn generate() -> Self {
        let mut secret = [0u8; 32];
        rand::rngs::OsRng.fill_bytes(&mut secret);
        let signing_key = SigningKey::from_bytes(&secret);
        let verifying_key = signing_key.verifying_key();
        Self {
            signing_key,
            verifying_key,
        }
    }

    pub fn sign(&self, message: &[u8]) -> Vec<u8> {
        let sig: Signature = self.signing_key.sign(message);
        sig.to_bytes().to_vec()
    }

    pub fn verify(&self, message: &[u8], signature_bytes: &[u8]) -> bool {
        if signature_bytes.len() != 64 {
            return false;
        }
        let mut arr = [0u8; 64];
        arr.copy_from_slice(signature_bytes);
        let sig = Signature::from_bytes(&arr);
        self.verifying_key.verify(message, &sig).is_ok()
    }

    pub fn public_hex(&self) -> String {
        hex::encode(self.verifying_key.to_bytes())
    }
}

pub struct RustReplayFilter {
    window_size: u32,
    highest_seq: HashMap<String, u32>,
    seen_seqs: HashMap<String, HashSet<u32>>,
}

impl RustReplayFilter {
    pub fn new(window_size: u32) -> Self {
        Self {
            window_size,
            highest_seq: HashMap::new(),
            seen_seqs: HashMap::new(),
        }
    }

    pub fn is_valid_and_update(&mut self, sender_id: &str, sequence: u32) -> bool {
        if sequence == 0 {
            return false;
        }

        let highest = self.highest_seq.entry(sender_id.to_string()).or_insert(0);
        let seen = self.seen_seqs.entry(sender_id.to_string()).or_default();

        if *highest == 0 {
            *highest = sequence;
            seen.insert(sequence);
            return true;
        }

        if sequence > *highest {
            *highest = sequence;
            seen.insert(sequence);
            let cutoff = if sequence > self.window_size { sequence - self.window_size } else { 0 };
            seen.retain(|&s| s > cutoff);
            return true;
        }

        if sequence <= highest.saturating_sub(self.window_size) {
            return false; // too old
        }

        if seen.contains(&sequence) {
            return false; // duplicate
        }

        seen.insert(sequence);
        true
    }
}
