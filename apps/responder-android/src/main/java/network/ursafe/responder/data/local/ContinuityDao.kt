package network.ursafe.responder.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

/**
 * UrSafe Phase 4: Room DAO for Responder Continuity Outbox
 */
@Dao
interface ContinuityDao {

    @Query("SELECT * FROM responder_continuity_messages WHERE messageId = :id")
    suspend fun getById(id: String): ContinuityMessageEntity?

    @Query("""
        SELECT * FROM responder_continuity_messages 
        WHERE currentState IN ('QUEUED', 'SCHEDULED', 'RETRY_WAIT')
          AND nextRetryAt <= :now
          AND expiresAt > :now
        ORDER BY priority ASC, nextRetryAt ASC, createdAt ASC
        LIMIT :limit
    """)
    suspend fun getPendingBatch(now: Long, limit: Int = 10): List<ContinuityMessageEntity>

    @Query("SELECT * FROM responder_continuity_messages ORDER BY createdAt DESC")
    fun getAllMessagesFlow(): Flow<List<ContinuityMessageEntity>>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertOrIgnore(message: ContinuityMessageEntity): Long

    @Update
    suspend fun update(message: ContinuityMessageEntity)

    @Query("""
        UPDATE responder_continuity_messages 
        SET currentState = 'RETRY_WAIT', nextRetryAt = 0, lastError = 'RECOVERED_AFTER_PROCESS_DEATH'
        WHERE currentState IN ('TRANSMITTING', 'SCHEDULED')
    """)
    suspend fun recoverInFlightMessages(): Int

    @Query("""
        UPDATE responder_continuity_messages 
        SET currentState = :newState, ackLevel = :ackLevel, completedAt = :now, lastError = NULL
        WHERE messageId = :messageId
    """)
    suspend fun markDelivered(messageId: String, newState: String, ackLevel: String, now: Long)

    @Query("""
        UPDATE responder_continuity_messages 
        SET currentState = 'RETRY_WAIT', attemptCount = :attemptCount, lastAttemptAt = :now, nextRetryAt = :nextRetryAt, lastError = :error
        WHERE messageId = :messageId
    """)
    suspend fun markRetry(messageId: String, attemptCount: Int, now: Long, nextRetryAt: Long, error: String)
}
