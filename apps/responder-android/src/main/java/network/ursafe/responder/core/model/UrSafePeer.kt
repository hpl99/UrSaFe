package network.ursafe.responder.core.model

enum class PeerConnectionState {
    DISCOVERED, CONNECTING, CONNECTED, GATT_READY, HANDSHAKING, AUTHENTICATED, TRUSTED, READY, DISCONNECTED, RECONNECTING, FAILED
}

enum class PeerAuthState {
    NONE, CHALLENGED, VERIFIED_PASSPORT, AUTHENTICATED
}

enum class PeerTrustState {
    UNTRUSTED, PENDING_VERIFICATION, TRUSTED_COMMUNITY, TRUSTED_OFFICIAL
}

data class UrSafePeer(
    val deviceId: String,
    val bluetoothAddress: String,
    val displayName: String,
    val role: UserRole = UserRole.CITIZEN,
    val connectionState: PeerConnectionState = PeerConnectionState.DISCOVERED,
    val authState: PeerAuthState = PeerAuthState.NONE,
    val trustState: PeerTrustState = PeerTrustState.UNTRUSTED,
    val rssiDbm: Int = -70,
    val batteryPercent: Int = 100,
    val lastSeenMs: Long = System.currentTimeMillis(),
    val capabilities: List<String> = listOf("BLE_DIRECT", "LORA_MESH", "OFFLINE_OUTBOX"),
    val isResponder: Boolean = (role == UserRole.RESPONDER || role == UserRole.AUTHORITY)
)
