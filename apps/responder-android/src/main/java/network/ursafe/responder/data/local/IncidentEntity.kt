package network.ursafe.responder.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "responder_incidents")
data class IncidentEntity(
    @PrimaryKey
    val incidentId: String,
    val category: String,
    val urgency: String,
    val peopleAffected: Int,
    val latitude: Double,
    val longitude: Double,
    val distanceKm: Double,
    val etaMinutes: Double,
    val skillMatchPercent: Int,
    val hazardRiskLevel: String, // LOW, MEDIUM, HIGH, DEADLY
    val networkReliabilityPercent: Int,
    val status: String, // NEW_ALERT, ACCEPTED, EN_ROUTE, ARRIVED, COMPLETED, DECLINED
    val receivedAtEpochMs: Long,
    val victimNotes: String,
    val victimContact: String?
)

@Dao
interface IncidentDao {
    @Query("SELECT * FROM responder_incidents WHERE status != 'DECLINED' ORDER BY CASE urgency WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END ASC, distanceKm ASC")
    fun getActiveIncidentsFlow(): Flow<List<IncidentEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(incident: IncidentEntity)

    @Query("UPDATE responder_incidents SET status = :newStatus WHERE incidentId = :id")
    suspend fun updateStatus(id: String, newStatus: String)
}
