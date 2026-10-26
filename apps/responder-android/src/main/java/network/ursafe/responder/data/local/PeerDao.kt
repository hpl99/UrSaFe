package network.ursafe.responder.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface PeerDao {
    @Query("SELECT * FROM responder_discovered_peers ORDER BY lastSeenMs DESC")
    fun getAllPeersFlow(): Flow<List<PeerEntity>>

    @Query("SELECT * FROM responder_discovered_peers WHERE deviceId = :id")
    suspend fun getById(id: String): PeerEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(peer: PeerEntity)

    @Query("UPDATE responder_discovered_peers SET connectionState = :state, lastSeenMs = :now WHERE deviceId = :id")
    suspend fun updateState(id: String, state: String, now: Long)
}

@Database(
    entities = [IncidentEntity::class, ContinuityMessageEntity::class, PeerEntity::class],
    version = 2,
    exportSchema = false
)
abstract class ResponderDatabase : RoomDatabase() {
    abstract fun incidentDao(): IncidentDao
    abstract fun continuityDao(): ContinuityDao
    abstract fun peerDao(): PeerDao
}
