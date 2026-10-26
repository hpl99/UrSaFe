package network.ursafe.victim.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface PeerDao {
    @Query("SELECT * FROM discovered_peers ORDER BY lastSeenMs DESC")
    fun getAllPeersFlow(): Flow<List<PeerEntity>>

    @Query("SELECT * FROM discovered_peers WHERE deviceId = :id")
    suspend fun getById(id: String): PeerEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(peer: PeerEntity)

    @Query("UPDATE discovered_peers SET connectionState = :state, lastSeenMs = :now WHERE deviceId = :id")
    suspend fun updateState(id: String, state: String, now: Long)

    @Query("DELETE FROM discovered_peers WHERE lastSeenMs < :thresholdMs")
    suspend fun purgeStale(thresholdMs: Long)
}
