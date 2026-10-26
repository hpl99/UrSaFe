package network.ursafe.victim.core.model

import java.security.MessageDigest
import java.util.UUID

enum class Priority(val code: Int) {
    CRITICAL_SOS(0),       // Life-critical emergency SOS, cancellation
    RESPONDER_ACK(1),      // Responder acceptance, dispatch, status
    HAZARD_ALERT(2),       // Real-time hazard boundary warning
    LOCATION_UPDATE(3),    // GPS coordinate update
    EVIDENCE_CHUNK(4),     // Document & photo transfer chunk
    NORMAL_MESSAGE(5),     // Peer text message
    TELEMETRY(6);          // Radio battery, node discovery, RSSI

    companion object {
        fun fromCode(code: Int): Priority = values().find { it.code == code } ?: NORMAL_MESSAGE
    }
}

enum class DeliveryState {
    CREATED,
    QUEUED,
    TRANSMITTING,
    SENT,
    RECEIVED,
    PERSISTED,
    ACKNOWLEDGED,
    DELIVERED,
    FAILED,
    RETRYING,
    EXPIRED
}

enum class UserRole {
    CITIZEN,
    RESPONDER,
    AUTHORITY,
    ADMIN
}

data class MessageEnvelope(
    val messageId: String = "msg-${System.currentTimeMillis().toString(36)}-${UUID.randomUUID().toString().take(8)}",
    val senderId: String,
    val senderRole: UserRole = UserRole.CITIZEN,
    val senderName: String,
    val recipientId: String = "BROADCAST",
    val messageType: String, // "SOS_CREATED", "SOS_ACK", "PEER_MSG", "EVIDENCE_CHUNK", "STATUS"
    val priority: Priority = Priority.CRITICAL_SOS,
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
