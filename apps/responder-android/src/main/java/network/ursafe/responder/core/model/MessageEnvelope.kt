package network.ursafe.responder.core.model

import java.security.MessageDigest
import java.util.UUID

enum class Priority(val code: Int) {
    CRITICAL_SOS(0),
    RESPONDER_ACK(1),
    HAZARD_ALERT(2),
    LOCATION_UPDATE(3),
    EVIDENCE_CHUNK(4),
    NORMAL_MESSAGE(5),
    TELEMETRY(6);

    companion object {
        fun fromCode(code: Int): Priority = values().find { it.code == code } ?: NORMAL_MESSAGE
    }
}

enum class DeliveryState {
    CREATED, QUEUED, TRANSMITTING, SENT, RECEIVED, PERSISTED, ACKNOWLEDGED, DELIVERED, FAILED, RETRYING, EXPIRED
}

enum class UserRole {
    CITIZEN, RESPONDER, AUTHORITY, ADMIN
}

data class MessageEnvelope(
    val messageId: String = "msg-${System.currentTimeMillis().toString(36)}-${UUID.randomUUID().toString().take(8)}",
    val senderId: String,
    val senderRole: UserRole = UserRole.RESPONDER,
    val senderName: String,
    val recipientId: String = "BROADCAST",
    val messageType: String,
    val priority: Priority = Priority.RESPONDER_ACK,
    val createdAtEpochMs: Long = System.currentTimeMillis(),
    val expiresAtEpochMs: Long = System.currentTimeMillis() + 86400000L,
    val sequenceNumber: Int = 1,
    val hopLimit: Int = 7,
    val originNodeId: String = senderId,
    val currentHopNodeId: String = senderId,
    val payloadJson: String,
    val payloadHash: String = sha256Hex(payloadJson),
    val signatureHex: String = "",
    val deliveryState: DeliveryState = DeliveryState.CREATED,
    val chunkIndex: Int = 0,
    val totalChunks: Int = 1,
    val transferId: String? = null
) {
    companion object {
        fun sha256Hex(input: String): String {
            val digest = MessageDigest.getInstance("SHA-256")
            val hashBytes = digest.digest(input.toByteArray(Charsets.UTF_8))
            return hashBytes.joinToString("") { "%02x".format(it) }
        }
    }
}
