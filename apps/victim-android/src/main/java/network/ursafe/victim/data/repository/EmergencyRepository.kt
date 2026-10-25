package network.ursafe.victim.data.repository

import network.ursafe.victim.data.local.EmergencyDao
import network.ursafe.victim.data.local.EmergencyEntity
import kotlinx.coroutines.flow.Flow
import java.util.UUID

class EmergencyRepository(private val dao: EmergencyDao) {
    val activeEmergency: Flow<EmergencyEntity?> = dao.getActiveEmergencyFlow()

    suspend fun createOfflineSos(
        category: String,
        urgency: String,
        peopleCount: Int,
        lat: Double,
        lon: Double,
        altitude: Float,
        description: String,
        signatureHex: String
    ): EmergencyEntity {
        val now = System.currentTimeMillis()
        val entity = EmergencyEntity(
            emergencyId = UUID.randomUUID().toString(),
            category = category,
            urgency = urgency,
            peopleAffected = peopleCount,
            latitude = lat,
            longitude = lon,
            altitudeMeters = altitude,
            textDescription = description,
            status = "QUEUED_LOCAL",
            responderCallsign = null,
            responderEtaMinutes = null,
            createdAtEpochMs = now,
            updatedAtEpochMs = now,
            signatureHex = signatureHex,
            isDelivered = false
        )
        dao.insertOrUpdate(entity)
        return entity
    }

    suspend fun updateMeshAck(emergencyId: String, responderCallsign: String, etaMinutes: Int) {
        val now = System.currentTimeMillis()
        dao.updateStatus(emergencyId, "ACKNOWLEDGED", responderCallsign, etaMinutes, now)
        dao.markDelivered(emergencyId)
    }

    suspend fun cancelEmergency(emergencyId: String) {
        val now = System.currentTimeMillis()
        dao.updateStatus(emergencyId, "CANCELLED", null, null, now)
    }
}
