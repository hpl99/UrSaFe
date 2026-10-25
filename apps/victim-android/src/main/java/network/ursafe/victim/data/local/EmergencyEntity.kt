package network.ursafe.victim.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "emergencies")
data class EmergencyEntity(
    @PrimaryKey
    val emergencyId: String,
    val category: String,
    val urgency: String,
    val peopleAffected: Int,
    val latitude: Double,
    val longitude: Double,
    val altitudeMeters: Float,
    val textDescription: String,
    val status: String, // CREATED, QUEUED_LOCAL, TRANSMITTED_MESH, ACKNOWLEDGED, HELP_ARRIVED
    val responderCallsign: String?,
    val responderEtaMinutes: Int?,
    val createdAtEpochMs: Long,
    val updatedAtEpochMs: Long,
    val signatureHex: String,
    val isDelivered: Boolean = false
)
