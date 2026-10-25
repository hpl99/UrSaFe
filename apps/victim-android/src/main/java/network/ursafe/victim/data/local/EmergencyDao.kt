package network.ursafe.victim.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface EmergencyDao {
    @Query("SELECT * FROM emergencies ORDER BY createdAtEpochMs DESC LIMIT 1")
    fun getActiveEmergencyFlow(): Flow<EmergencyEntity?>

    @Query("SELECT * FROM emergencies WHERE emergencyId = :id")
    suspend fun getById(id: String): EmergencyEntity?

    @Query("SELECT * FROM emergencies WHERE isDelivered = 0 ORDER BY createdAtEpochMs ASC")
    suspend fun getPendingOutbox(): List<EmergencyEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(emergency: EmergencyEntity)

    @Query("UPDATE emergencies SET status = :status, responderCallsign = :callsign, responderEtaMinutes = :eta, updatedAtEpochMs = :now WHERE emergencyId = :id")
    suspend fun updateStatus(id: String, status: String, callsign: String?, eta: Int?, now: Long)

    @Query("UPDATE emergencies SET isDelivered = 1 WHERE emergencyId = :id")
    suspend fun markDelivered(id: String)
}

@Database(entities = [EmergencyEntity::class], version = 1, exportSchema = false)
abstract class UrsafeDatabase : RoomDatabase() {
    abstract fun emergencyDao(): EmergencyDao
}
