package network.ursafe.responder.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * UrSafe Phase 4: Production Android Responder Continuity Message Entity
 * Backed by durable SQLite Room WAL storage.
 * Tracks outbound mission acknowledgements and lifecycle transitions.
 */
@Entity(
    tableName = "responder_continuity_messages",
    indices = [
        Index(value = ["priority", "nextRetryAt", "createdAt"]),
        Index(value = ["currentState", "expiresAt"])
    ]
)
data class ContinuityMessageEntity(
    @PrimaryKey
    val messageId: String,
    val incidentId: String?,
    val senderDeviceId: String,
    val senderUserId: String?,
    val recipientScope: String = "BROADCAST",
    val messageType: String,
    val priority: Int = 2, // 2=P2_RESPONDER_OPERATION
    val createdAt: Long,
    val expiresAt: Long,
    val sequenceNumber: Int = 1,
    val payloadJson: String,
    val payloadHash: String,
    val deliveryPolicyJson: String? = null,
    val currentState: String = "QUEUED",
    val attemptCount: Int = 0,
    val lastAttemptAt: Long? = null,
    val nextRetryAt: Long = 0L,
    val lastTransport: String? = null,
    val lastError: String? = null,
    val ackLevel: String = "NONE",
    val completedAt: Long? = null
)
