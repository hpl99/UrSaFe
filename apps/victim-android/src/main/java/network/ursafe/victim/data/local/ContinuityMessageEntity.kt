package network.ursafe.victim.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * UrSafe Phase 4: Production-Grade Android Continuity Message Entity
 * Backed by durable SQLite Room WAL storage.
 * Enforces strict P0 preemption and delivery state tracking.
 */
@Entity(
    tableName = "continuity_messages",
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
    val priority: Int = 0, // 0=P0_LIFE_CRITICAL, 1=P1_CONTROL, 2=P2_OPERATION, 3=P3_SAFETY, 4=P4_NORMAL, 5=P5_TELEMETRY
    val createdAt: Long,
    val expiresAt: Long,
    val sequenceNumber: Int = 1,
    val payloadJson: String,
    val payloadHash: String,
    val deliveryPolicyJson: String? = null,
    val currentState: String = "QUEUED", // QUEUED, TRANSMITTING, SENT, DELIVERED, ACKNOWLEDGED, RETRY_WAIT, EXPIRED, DEAD_LETTER
    val attemptCount: Int = 0,
    val lastAttemptAt: Long? = null,
    val nextRetryAt: Long = 0L,
    val lastTransport: String? = null,
    val lastError: String? = null,
    val ackLevel: String = "NONE", // NONE, TRANSPORT_ACK, NODE_ACK, APPLICATION_ACK, HUMAN_ACK
    val completedAt: Long? = null
)
