package network.ursafe.responder.core.engine

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import network.ursafe.responder.core.model.*
import network.ursafe.responder.core.notification.EmergencyNotificationManager
import network.ursafe.responder.core.transport.BleGattManager
import network.ursafe.responder.core.transport.MeshtasticRadioTransport
import network.ursafe.responder.data.local.ContinuityDao
import network.ursafe.responder.data.local.ContinuityMessageEntity
import network.ursafe.responder.data.local.IncidentDao
import network.ursafe.responder.data.local.IncidentEntity
import java.util.*

data class MeshNetworkDiagnostics(
    val connectedBlePeersCount: Int = 0,
    val radioConnected: Boolean = true,
    val radioNodesCount: Int = 6,
    val pendingOutboxCount: Int = 0,
    val deliveredCount: Int = 0,
    val totalTransmittedPackets: Int = 0
)

class MeshTransportEngine(
    private val context: Context,
    private val continuityDao: ContinuityDao,
    private val incidentDao: IncidentDao,
    val myDeviceId: String = "resp-${UUID.randomUUID().toString().take(8)}",
    val myName: String = "Capt. Vikram Singh (NDRF-B-108)",
    val myRole: UserRole = UserRole.RESPONDER
) {
    companion object {
        private const val TAG = "UrSafe_Responder_Engine"
    }

    val notificationManager = EmergencyNotificationManager(context)
    val bleGattManager = BleGattManager(context, myDeviceId, myName, myRole, notificationManager)
    val radioTransport = MeshtasticRadioTransport(context, notificationManager)

    private val _diagnostics = MutableStateFlow(MeshNetworkDiagnostics())
    val diagnostics: StateFlow<MeshNetworkDiagnostics> = _diagnostics.asStateFlow()

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    init {
        setupListeners()
    }

    private fun setupListeners() {
        bleGattManager.onEnvelopeReceivedListener = { envelope ->
            scope.launch {
                handleIncomingEnvelope(envelope, "BLE_DIRECT")
            }
        }

        radioTransport.onRadioPacketReceivedListener = { envelope, rssi, snr, hops ->
            scope.launch {
                handleIncomingEnvelope(envelope, "MESHTASTIC_LORA")
            }
        }
    }

    suspend fun updateMissionState(incidentId: String, newState: String): Boolean {
        incidentDao.updateStatus(incidentId, newState)

        val payloadJson = """{"incidentId":"$incidentId","responderId":"$myDeviceId","action":"$newState","timestamp":${System.currentTimeMillis()}}"""
        val envelope = MessageEnvelope(
            senderId = myDeviceId,
            senderRole = myRole,
            senderName = myName,
            messageType = "SOS_STATUS_UPDATE",
            priority = Priority.RESPONDER_ACK,
            payloadJson = payloadJson
        )

        val sentBle = bleGattManager.broadcastEnvelope(envelope)
        val sentLora = radioTransport.transmitMeshPacket(envelope)

        val now = System.currentTimeMillis()
        val continuityMessage = ContinuityMessageEntity(
            messageId = envelope.messageId,
            incidentId = incidentId,
            senderDeviceId = myDeviceId,
            senderUserId = myDeviceId,
            messageType = "SOS_STATUS_UPDATE",
            priority = 2,
            createdAt = now,
            expiresAt = now + 86400000L,
            payloadJson = payloadJson,
            payloadHash = envelope.payloadHash,
            currentState = if (sentBle > 0 || sentLora) "SENT" else "QUEUED"
        )

        continuityDao.insertOrIgnore(continuityMessage)
        return sentBle > 0 || sentLora
    }

    suspend fun sendPeerMessage(peerAddress: String, text: String): Boolean {
        val envelope = MessageEnvelope(
            senderId = myDeviceId,
            senderRole = myRole,
            senderName = myName,
            recipientId = peerAddress,
            messageType = "PEER_MSG",
            priority = Priority.NORMAL_MESSAGE,
            payloadJson = text
        )

        return bleGattManager.sendEnvelope(peerAddress, envelope)
    }

    private suspend fun handleIncomingEnvelope(envelope: MessageEnvelope, transport: String) {
        val now = System.currentTimeMillis()
        val continuityEntity = ContinuityMessageEntity(
            messageId = envelope.messageId,
            incidentId = null,
            senderDeviceId = envelope.senderId,
            senderUserId = envelope.senderId,
            messageType = envelope.messageType,
            priority = envelope.priority.code,
            createdAt = envelope.createdAtEpochMs,
            expiresAt = envelope.expiresAtEpochMs,
            payloadJson = envelope.payloadJson,
            payloadHash = envelope.payloadHash,
            currentState = "RECEIVED",
            lastTransport = transport,
            completedAt = now
        )

        continuityDao.insertOrIgnore(continuityEntity)

        if (envelope.messageType == "SOS_CREATED" || envelope.priority == Priority.CRITICAL_SOS) {
            val incident = IncidentEntity(
                incidentId = envelope.messageId,
                category = "FLOOD",
                urgency = "CRITICAL",
                peopleAffected = 2,
                latitude = 19.0760,
                longitude = 72.8777,
                distanceKm = 1.2,
                etaMinutes = 6.0,
                skillMatchPercent = 95,
                hazardRiskLevel = "HIGH",
                networkReliabilityPercent = 88,
                status = "NEW_ALERT",
                receivedAtEpochMs = now,
                victimNotes = envelope.payloadJson,
                victimContact = envelope.senderName
            )
            incidentDao.insertOrUpdate(incident)
        }
    }
}
