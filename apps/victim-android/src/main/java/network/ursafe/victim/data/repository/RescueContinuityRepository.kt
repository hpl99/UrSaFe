package network.ursafe.victim.data.repository

import network.ursafe.victim.data.local.ContinuityDao
import network.ursafe.victim.data.local.ContinuityMessageEntity
import kotlinx.coroutines.flow.Flow
import java.security.MessageDigest
import java.util.UUID
import kotlin.math.min
import kotlin.math.pow
import kotlin.random.Random

/**
 * UrSafe Phase 4: Production Android Rescue Continuity Repository
 * Guarantees zero emergency message loss during network loss, app crashes, and device reboots.
 */
class RescueContinuityRepository(private val dao: ContinuityDao) {

    val allMessages: Flow<List<ContinuityMessageEntity>> = dao.getAllMessagesFlow()

    /**
     * Section 13: Boot / Process-Death Recovery Routine
     * Resets any messages interrupted during transmission back to RETRY_WAIT so they are not abandoned.
     */
    suspend fun recoverPendingOnStartup(): Int {
        return dao.recoverInFlightMessages()
    }

    /**
     * Section 11: Durable Outbox Enqueue
     * Writes to local SQLite Room database before any transport transmission is attempted.
     */
    suspend fun enqueueP0Sos(
        incidentId: String,
        deviceId: String,
        userId: String?,
        payloadJson: String
    ): ContinuityMessageEntity {
        val now = System.currentTimeMillis()
        val messageId = "msg-${now.toString(36)}-${UUID.randomUUID().toString().take(8)}"
        val hash = sha256(payloadJson)
        val expiresAt = now + 86400000L // 24 hours validity

        val entity = ContinuityMessageEntity(
            messageId = messageId,
            incidentId = incidentId,
            senderDeviceId = deviceId,
            senderUserId = userId,
            recipientScope = "BROADCAST",
            messageType = "SOS_CREATE",
            priority = 0, // P0 LIFE CRITICAL
            createdAt = now,
            expiresAt = expiresAt,
            payloadJson = payloadJson,
            payloadHash = hash,
            currentState = "QUEUED",
            attemptCount = 0,
            nextRetryAt = 0L,
            ackLevel = "NONE"
        )

        // Durable commit
        dao.insertOrIgnore(entity)
        return entity
    }

    /**
     * Section 19: Compute Bounded Exponential Backoff with Jitter
     */
    fun computeNextRetry(priority: Int, attemptCount: Int): Long {
        val now = System.currentTimeMillis()
        val baseDelayMs = if (priority <= 1) 2000L else 5000L
        val factor = if (priority <= 1) 1.5 else 2.0
        val maxDelayMs = if (priority <= 1) 15000L else 120000L

        val rawDelay = min(maxDelayMs, (baseDelayMs * factor.pow((attemptCount - 1).coerceAtLeast(0).toDouble())).toLong())
        val jitter = (Random.nextDouble(-0.2, 0.2) * rawDelay).toLong()
        val finalDelay = (rawDelay + jitter).coerceAtLeast(1000L)

        return now + finalDelay
    }

    /**
     * Section 30: Human-Readable Delivery Explanation
     */
    fun getDeliveryExplanation(entity: ContinuityMessageEntity): String {
        return when (entity.currentState) {
            "ACKNOWLEDGED" -> "Responder has acknowledged and verified your emergency."
            "DELIVERED" -> "Transmitted via ${entity.lastTransport ?: "radio bearer"}. Awaiting responder confirmation."
            "TRANSMITTING" -> "Actively transmitting over ${entity.lastTransport ?: "emergency radio"}..."
            "QUEUED" -> "Saved securely on device. Searching for viable emergency mesh paths."
            "RETRY_WAIT" -> {
                val sec = ((entity.nextRetryAt - System.currentTimeMillis()) / 1000L).coerceAtLeast(0L)
                "Waiting to retry (attempt ${entity.attemptCount}). Next retry in ~${sec}s."
            }
            "DEAD_LETTER" -> "Max delivery attempts reached. Retained securely in emergency audit store."
            "EXPIRED" -> "Message validity period expired."
            else -> "Status pending transport resolution."
        }
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
