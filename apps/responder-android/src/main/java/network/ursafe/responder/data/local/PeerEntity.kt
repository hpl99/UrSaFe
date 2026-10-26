package network.ursafe.responder.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "responder_discovered_peers")
data class PeerEntity(
    @PrimaryKey
    val deviceId: String,
    val bluetoothAddress: String,
    val displayName: String,
    val role: String,
    val connectionState: String,
    val authState: String,
    val trustState: String,
    val rssiDbm: Int,
    val batteryPercent: Int,
    val lastSeenMs: Long,
    val capabilitiesCsv: String
)
