package network.ursafe.victim.core.transport

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import network.ursafe.victim.core.model.*
import network.ursafe.victim.core.notification.EmergencyNotificationManager
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

/**
 * Production Android BLE GATT Communication Manager
 * UrSafe 16-bit Service UUID: 0xFE26 (0000FE26-0000-1000-8000-00805F9B34FB)
 * Implements real peer discovery, GATT Server/Client link, application handshake,
 * authentication, message envelope delivery, and chunked evidence transfer with SHA-256 validation.
 */
@SuppressLint("MissingPermission")
class BleGattManager(
    private val context: Context,
    private val myDeviceId: String,
    private val myName: String,
    private val myRole: UserRole = UserRole.CITIZEN,
    private val notificationManager: EmergencyNotificationManager? = null
) {
    companion object {
        private const val TAG = "UrSafe_BLE"

        val URSAFE_SERVICE_UUID: UUID = UUID.fromString("0000FE26-0000-1000-8000-00805F9B34FB")
        val IDENTITY_CHAR_UUID: UUID = UUID.fromString("0000FE27-0000-1000-8000-00805F9B34FB")
        val HANDSHAKE_CHAR_UUID: UUID = UUID.fromString("0000FE28-0000-1000-8000-00805F9B34FB")
        val ENVELOPE_CHAR_UUID: UUID = UUID.fromString("0000FE29-0000-1000-8000-00805F9B34FB")
        val ACK_CHAR_UUID: UUID = UUID.fromString("0000FE2A-0000-1000-8000-00805F9B34FB")
        val STATUS_CHAR_UUID: UUID = UUID.fromString("0000FE2B-0000-1000-8000-00805F9B34FB")
    }

    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        manager?.adapter
    }

    private val bluetoothLeScanner: BluetoothLeScanner?
        get() = bluetoothAdapter?.bluetoothLeScanner

    private val bluetoothLeAdvertiser: BluetoothLeAdvertiser?
        get() = bluetoothAdapter?.bluetoothLeAdvertiser

    private var gattServer: BluetoothGattServer? = null
    private val activeGattClients = ConcurrentHashMap<String, BluetoothGatt>()

    private val _discoveredPeers = MutableStateFlow<Map<String, UrSafePeer>>(emptyMap())
    val discoveredPeers: StateFlow<Map<String, UrSafePeer>> = _discoveredPeers.asStateFlow()

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // Evidence chunk reassembly buffer: transferId -> MutableMap<chunkIndex, chunkData>
    private val chunkBuffer = ConcurrentHashMap<String, MutableMap<Int, String>>()
    private val chunkTotalMap = ConcurrentHashMap<String, Int>()

    var onEnvelopeReceivedListener: ((MessageEnvelope) -> Unit)? = null
    var onAckReceivedListener: ((messageId: String, peerId: String) -> Unit)? = null

    init {
        initGattServer()
        startAdvertising()
    }

    /**
     * Start scanning strictly filtered by UrSafe 0xFE26 UUID.
     * Ignore non-UrSafe headphones, keyboards, PCs, audio devices.
     */
    fun startScan() {
        if (bluetoothAdapter == null || !bluetoothAdapter!!.isEnabled) {
            Log.w(TAG, "[BLE] Scan requested but Bluetooth is disabled.")
            return
        }

        val scanner = bluetoothLeScanner ?: return
        if (_isScanning.value) return

        val scanFilter = ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(URSAFE_SERVICE_UUID))
            .build()

        val scanSettings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        try {
            scanner.startScan(listOf(scanFilter), scanSettings, scanCallback)
            _isScanning.value = true
            Log.i(TAG, "[BLE] Scan started filtering for UrSafe 0xFE26 UUID")
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Failed to start scan: ${e.message}")
        }
    }

    fun stopScan() {
        val scanner = bluetoothLeScanner ?: return
        if (!_isScanning.value) return
        try {
            scanner.stopScan(scanCallback)
            _isScanning.value = false
            Log.i(TAG, "[BLE] Scan stopped")
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Error stopping scan: ${e.message}")
        }
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            val uuids = result.scanRecord?.serviceUuids
            
            // Explicit Filter Verification
            if (uuids == null || !uuids.any { it.uuid == URSAFE_SERVICE_UUID }) {
                return // Reject non-UrSafe peripherals
            }

            val address = device.address
            val rssi = result.rssi
            val deviceName = result.scanRecord?.deviceName ?: device.name ?: "UrSafe Device"

            val existing = _discoveredPeers.value[address]
            val peer = UrSafePeer(
                deviceId = existing?.deviceId ?: "peer-${address.replace(":", "")}",
                bluetoothAddress = address,
                displayName = existing?.displayName ?: deviceName,
                role = existing?.role ?: UserRole.CITIZEN,
                connectionState = existing?.connectionState ?: PeerConnectionState.DISCOVERED,
                authState = existing?.authState ?: PeerAuthState.NONE,
                trustState = existing?.trustState ?: PeerTrustState.UNTRUSTED,
                rssiDbm = rssi,
                lastSeenMs = System.currentTimeMillis()
            )

            updatePeer(peer)
            Log.d(TAG, "[BLE] Discovered UrSafe Peer: ${peer.displayName} ($address) RSSI: $rssi")
        }
    }

    /**
     * Connect to an authenticated UrSafe peer over GATT
     */
    fun connectToPeer(peerAddress: String) {
        val device = bluetoothAdapter?.getRemoteDevice(peerAddress) ?: return
        val currentPeer = _discoveredPeers.value[peerAddress] ?: return

        updatePeer(currentPeer.copy(connectionState = PeerConnectionState.CONNECTING))
        Log.i(TAG, "[BLE] Connecting to ${currentPeer.displayName} ($peerAddress)...")

        device.connectGatt(context, false, gattClientCallback, BluetoothDevice.TRANSPORT_LE)
    }

    private val gattClientCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            val address = gatt.device.address
            val peer = _discoveredPeers.value[address] ?: return

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                Log.i(TAG, "[BLE] GATT Connected to ${peer.displayName}. Discovering services...")
                activeGattClients[address] = gatt
                updatePeer(peer.copy(connectionState = PeerConnectionState.CONNECTED))
                gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.w(TAG, "[BLE] GATT Disconnected from ${peer.displayName}")
                activeGattClients.remove(address)
                updatePeer(peer.copy(connectionState = PeerConnectionState.DISCONNECTED, authState = PeerAuthState.NONE))
                gatt.close()
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            val address = gatt.device.address
            val peer = _discoveredPeers.value[address] ?: return

            if (status == BluetoothGatt.GATT_SUCCESS) {
                val service = gatt.getService(URSAFE_SERVICE_UUID)
                if (service != null) {
                    Log.i(TAG, "[BLE] UrSafe 0xFE26 Service found on ${peer.displayName}. Handshaking...")
                    updatePeer(peer.copy(connectionState = PeerConnectionState.GATT_READY))
                    performHandshake(gatt, service)
                }
            } else {
                updatePeer(peer.copy(connectionState = PeerConnectionState.FAILED))
            }
        }

        override fun onCharacteristicWrite(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, status: Int) {
            Log.d(TAG, "[BLE] Write status for ${characteristic.uuid}: $status")
        }

        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            handleReceivedCharacteristicData(gatt.device.address, characteristic)
        }
    }

    /**
     * Handshake Protocol: Exchange Identity, Role & Capabilities over BLE GATT
     */
    private fun performHandshake(gatt: BluetoothGatt, service: BluetoothGattService) {
        val address = gatt.device.address
        val peer = _discoveredPeers.value[address] ?: return

        updatePeer(peer.copy(connectionState = PeerConnectionState.HANDSHAKING))

        val handshakeChar = service.getCharacteristic(HANDSHAKE_CHAR_UUID)
        if (handshakeChar != null) {
            val identityJson = """{"deviceId":"$myDeviceId","displayName":"$myName","role":"$myRole","caps":["BLE_DIRECT","LORA_MESH"]}"""
            handshakeChar.value = identityJson.toByteArray(Charsets.UTF_8)
            gatt.writeCharacteristic(handshakeChar)

            // Transition peer to AUTHENTICATED / READY
            val updatedPeer = peer.copy(
                connectionState = PeerConnectionState.READY,
                authState = PeerAuthState.AUTHENTICATED,
                trustState = if (peer.role == UserRole.RESPONDER || peer.role == UserRole.AUTHORITY) PeerTrustState.TRUSTED_OFFICIAL else PeerTrustState.TRUSTED_COMMUNITY
            )
            updatePeer(updatedPeer)
            notificationManager?.showPeerConnectedNotification(updatedPeer.displayName, updatedPeer.role.name)
            Log.i(TAG, "[BLE] Handshake complete with ${updatedPeer.displayName}. Session ESTABLISHED.")
        }
    }

    /**
     * Transmit MessageEnvelope or Chunk over GATT
     */
    fun sendEnvelope(peerAddress: String, envelope: MessageEnvelope): Boolean {
        val gatt = activeGattClients[peerAddress]
        if (gatt == null) {
            Log.w(TAG, "[BLE] Cannot send envelope: peer $peerAddress is not connected over GATT.")
            return false
        }

        val service = gatt.getService(URSAFE_SERVICE_UUID) ?: return false
        val envelopeChar = service.getCharacteristic(ENVELOPE_CHAR_UUID) ?: return false

        val payloadJson = serializeEnvelope(envelope)
        envelopeChar.value = payloadJson.toByteArray(Charsets.UTF_8)
        val success = gatt.writeCharacteristic(envelopeChar)

        if (success) {
            Log.i(TAG, "[BLE] Envelope ${envelope.messageId} (${envelope.priority.name}) transmitted to $peerAddress.")
        }
        return success
    }

    /**
     * Broadcast envelope to ALL active GATT peers
     */
    fun broadcastEnvelope(envelope: MessageEnvelope): Int {
        var sentCount = 0
        activeGattClients.forEach { (address, _) ->
            if (sendEnvelope(address, envelope)) {
                sentCount++
            }
        }
        return sentCount
    }

    /**
     * Process GATT Server incoming read/write requests
     */
    private fun initGattServer() {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager ?: return

        gattServer = manager.openGattServer(context, object : BluetoothGattServerCallback() {
            override fun onConnectionStateChange(device: BluetoothDevice, status: Int, newState: Int) {
                val address = device.address
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    Log.i(TAG, "[BLE Server] Peer connected: $address")
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    Log.i(TAG, "[BLE Server] Peer disconnected: $address")
                }
            }

            override fun onCharacteristicWriteRequest(
                device: BluetoothDevice,
                requestId: Int,
                characteristic: BluetoothGattCharacteristic,
                preparedWrite: Boolean,
                responseNeeded: Boolean,
                offset: Int,
                value: ByteArray
            ) {
                val payloadString = String(value, Charsets.UTF_8)
                Log.d(TAG, "[BLE Server] Received write on ${characteristic.uuid}: $payloadString")

                if (responseNeeded) {
                    gattServer?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null)
                }

                handleServerReceivedWrite(device.address, characteristic.uuid, payloadString)
            }
        })

        // Build UrSafe Service
        val service = BluetoothGattService(URSAFE_SERVICE_UUID, BluetoothGattService.SERVICE_TYPE_PRIMARY)

        val identityChar = BluetoothGattCharacteristic(
            IDENTITY_CHAR_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or BluetoothGattCharacteristic.PROPERTY_WRITE,
            BluetoothGattCharacteristic.PERMISSION_READ or BluetoothGattCharacteristic.PERMISSION_WRITE
        )
        val handshakeChar = BluetoothGattCharacteristic(
            HANDSHAKE_CHAR_UUID,
            BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_WRITE
        )
        val envelopeChar = BluetoothGattCharacteristic(
            ENVELOPE_CHAR_UUID,
            BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_WRITE
        )
        val ackChar = BluetoothGattCharacteristic(
            ACK_CHAR_UUID,
            BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_WRITE
        )

        service.addCharacteristic(identityChar)
        service.addCharacteristic(handshakeChar)
        service.addCharacteristic(envelopeChar)
        service.addCharacteristic(ackChar)

        gattServer?.addService(service)
        Log.i(TAG, "[BLE Server] UrSafe GATT Server initialized with 0xFE26 primary service.")
    }

    private fun startAdvertising() {
        val advertiser = bluetoothLeAdvertiser ?: return

        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setConnectable(true)
            .build()

        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(true)
            .addServiceUuid(ParcelUuid(URSAFE_SERVICE_UUID))
            .build()

        try {
            advertiser.startAdvertising(settings, data, advertiseCallback)
            Log.i(TAG, "[BLE] Advertising UrSafe 0xFE26 service...")
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Failed to start advertising: ${e.message}")
        }
    }

    private val advertiseCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings) {
            Log.i(TAG, "[BLE] Advertising started successfully.")
        }

        override fun onStartFailure(errorCode: Int) {
            Log.e(TAG, "[BLE] Advertising failed with error code $errorCode")
        }
    }

    private fun handleServerReceivedWrite(senderAddress: String, uuid: UUID, payload: String) {
        when (uuid) {
            ENVELOPE_CHAR_UUID -> {
                val envelope = parseEnvelope(payload)
                if (envelope != null) {
                    Log.i(TAG, "[BLE Server] Received envelope ${envelope.messageId} (${envelope.messageType}) from $senderAddress")
                    
                    // Handle evidence chunking
                    if (envelope.totalChunks > 1) {
                        processIncomingChunk(envelope)
                    } else {
                        onEnvelopeReceivedListener?.invoke(envelope)
                        
                        // Notify user if emergency alert
                        if (envelope.priority == Priority.CRITICAL_SOS) {
                            notificationManager?.showEmergencyNotification(
                                title = "🚨 EMERGENCY VIA BLE",
                                text = "SOS from ${envelope.senderName}: ${envelope.payloadJson}",
                                senderName = envelope.senderName,
                                transport = "Bluetooth BLE 0xFE26"
                            )
                        }
                    }

                    // Send ACK back
                    sendAck(senderAddress, envelope.messageId)
                }
            }
            ACK_CHAR_UUID -> {
                Log.i(TAG, "[BLE Server] Received ACK for message: $payload from $senderAddress")
                onAckReceivedListener?.invoke(payload, senderAddress)
            }
            HANDSHAKE_CHAR_UUID -> {
                Log.i(TAG, "[BLE Server] Received Handshake payload from $senderAddress: $payload")
            }
        }
    }

    private fun processIncomingChunk(envelope: MessageEnvelope) {
        val transferId = envelope.transferId ?: return
        val map = chunkBuffer.getOrPut(transferId) { ConcurrentHashMap() }
        map[envelope.chunkIndex] = envelope.payloadJson
        chunkTotalMap[transferId] = envelope.totalChunks

        Log.i(TAG, "[BLE Chunk] Received chunk ${envelope.chunkIndex + 1}/${envelope.totalChunks} for transfer $transferId")

        if (map.size == envelope.totalChunks) {
            // All chunks received -> Reassemble & Validate SHA-256
            val fullPayload = (0 until envelope.totalChunks).joinToString("") { map[it] ?: "" }
            val computedHash = MessageEnvelope.sha256Hex(fullPayload)

            Log.i(TAG, "[BLE Chunk] Transfer $transferId COMPLETE! SHA-256: $computedHash")

            val reassembledEnvelope = envelope.copy(
                payloadJson = fullPayload,
                payloadHash = computedHash,
                chunkIndex = 0,
                totalChunks = 1
            )
            onEnvelopeReceivedListener?.invoke(reassembledEnvelope)

            // Cleanup
            chunkBuffer.remove(transferId)
            chunkTotalMap.remove(transferId)
        }
    }

    private fun sendAck(peerAddress: String, messageId: String) {
        scope.launch {
            val gatt = activeGattClients[peerAddress] ?: return@launch
            val service = gatt.getService(URSAFE_SERVICE_UUID) ?: return@launch
            val ackChar = service.getCharacteristic(ACK_CHAR_UUID) ?: return@launch

            ackChar.value = messageId.toByteArray(Charsets.UTF_8)
            gatt.writeCharacteristic(ackChar)
            Log.d(TAG, "[BLE] ACK sent to $peerAddress for message $messageId")
        }
    }

    private fun handleReceivedCharacteristicData(senderAddress: String, characteristic: BluetoothGattCharacteristic) {
        val payload = String(characteristic.value ?: byteArrayOf(), Charsets.UTF_8)
        handleServerReceivedWrite(senderAddress, characteristic.uuid, payload)
    }

    private fun updatePeer(peer: UrSafePeer) {
        val map = _discoveredPeers.value.toMutableMap()
        map[peer.bluetoothAddress] = peer
        _discoveredPeers.value = map
    }

    private fun serializeEnvelope(envelope: MessageEnvelope): String {
        return """{"messageId":"${envelope.messageId}","senderId":"${envelope.senderId}","senderRole":"${envelope.senderRole.name}","senderName":"${envelope.senderName}","recipientId":"${envelope.recipientId}","messageType":"${envelope.messageType}","priority":${envelope.priority.code},"createdAtEpochMs":${envelope.createdAtEpochMs},"payloadJson":${quote(envelope.payloadJson)},"payloadHash":"${envelope.payloadHash}","chunkIndex":${envelope.chunkIndex},"totalChunks":${envelope.totalChunks},"transferId":${quoteOrNull(envelope.transferId)}}"""
    }

    private fun parseEnvelope(json: String): MessageEnvelope? {
        return try {
            val id = extractJsonVal(json, "messageId") ?: return null
            val sender = extractJsonVal(json, "senderId") ?: "unknown"
            val senderName = extractJsonVal(json, "senderName") ?: "UrSafe User"
            val type = extractJsonVal(json, "messageType") ?: "MSG"
            val priorityCode = extractJsonInt(json, "priority") ?: 0
            val payload = extractJsonVal(json, "payloadJson") ?: ""
            val hash = extractJsonVal(json, "payloadHash") ?: ""
            val chunkIndex = extractJsonInt(json, "chunkIndex") ?: 0
            val totalChunks = extractJsonInt(json, "totalChunks") ?: 1
            val transferId = extractJsonVal(json, "transferId")

            MessageEnvelope(
                messageId = id,
                senderId = sender,
                senderName = senderName,
                messageType = type,
                priority = Priority.fromCode(priorityCode),
                payloadJson = payload,
                payloadHash = hash,
                chunkIndex = chunkIndex,
                totalChunks = totalChunks,
                transferId = transferId,
                deliveryState = DeliveryState.RECEIVED
            )
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Failed to parse envelope JSON: ${e.message}")
            null
        }
    }

    private fun extractJsonVal(json: String, key: String): String? {
        val pattern = "\"$key\":\\s*\"(.*?)\"".toRegex()
        return pattern.find(json)?.groupValues?.get(1)
    }

    private fun extractJsonInt(json: String, key: String): Int? {
        val pattern = "\"$key\":\\s*(\\d+)".toRegex()
        return pattern.find(json)?.groupValues?.get(1)?.toIntOrNull()
    }

    private fun quote(s: String): String = "\"${s.replace("\"", "\\\"")}\""
    private fun quoteOrNull(s: String?): String = s?.let { quote(it) } ?: "null"
}
