package network.ursafe.responder.core.transport

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
import network.ursafe.responder.core.model.*
import network.ursafe.responder.core.notification.EmergencyNotificationManager
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

@SuppressLint("MissingPermission")
class BleGattManager(
    private val context: Context,
    private val myDeviceId: String,
    private val myName: String,
    private val myRole: UserRole = UserRole.RESPONDER,
    private val notificationManager: EmergencyNotificationManager? = null
) {
    companion object {
        private const val TAG = "UrSafe_Responder_BLE"

        val URSAFE_SERVICE_UUID: UUID = UUID.fromString("0000FE26-0000-1000-8000-00805F9B34FB")
        val IDENTITY_CHAR_UUID: UUID = UUID.fromString("0000FE27-0000-1000-8000-00805F9B34FB")
        val HANDSHAKE_CHAR_UUID: UUID = UUID.fromString("0000FE28-0000-1000-8000-00805F9B34FB")
        val ENVELOPE_CHAR_UUID: UUID = UUID.fromString("0000FE29-0000-1000-8000-00805F9B34FB")
        val ACK_CHAR_UUID: UUID = UUID.fromString("0000FE2A-0000-1000-8000-00805F9B34FB")
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

    private val chunkBuffer = ConcurrentHashMap<String, MutableMap<Int, String>>()
    private val chunkTotalMap = ConcurrentHashMap<String, Int>()

    var onEnvelopeReceivedListener: ((MessageEnvelope) -> Unit)? = null
    var onAckReceivedListener: ((messageId: String, peerId: String) -> Unit)? = null

    init {
        initGattServer()
        startAdvertising()
    }

    fun startScan() {
        if (bluetoothAdapter == null || !bluetoothAdapter!!.isEnabled) return
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
            Log.i(TAG, "[BLE] Responder Scan started filtering for 0xFE26 UUID")
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Scan error: ${e.message}")
        }
    }

    fun stopScan() {
        val scanner = bluetoothLeScanner ?: return
        if (!_isScanning.value) return
        try {
            scanner.stopScan(scanCallback)
            _isScanning.value = false
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Stop scan error: ${e.message}")
        }
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            val uuids = result.scanRecord?.serviceUuids ?: return
            if (!uuids.any { it.uuid == URSAFE_SERVICE_UUID }) return

            val address = device.address
            val rssi = result.rssi
            val deviceName = result.scanRecord?.deviceName ?: device.name ?: "UrSafe Peer"

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
        }
    }

    fun connectToPeer(peerAddress: String) {
        val device = bluetoothAdapter?.getRemoteDevice(peerAddress) ?: return
        val currentPeer = _discoveredPeers.value[peerAddress] ?: return

        updatePeer(currentPeer.copy(connectionState = PeerConnectionState.CONNECTING))
        device.connectGatt(context, false, gattClientCallback, BluetoothDevice.TRANSPORT_LE)
    }

    private val gattClientCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            val address = gatt.device.address
            val peer = _discoveredPeers.value[address] ?: return

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                activeGattClients[address] = gatt
                updatePeer(peer.copy(connectionState = PeerConnectionState.CONNECTED))
                gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                activeGattClients.remove(address)
                updatePeer(peer.copy(connectionState = PeerConnectionState.DISCONNECTED))
                gatt.close()
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            val address = gatt.device.address
            val peer = _discoveredPeers.value[address] ?: return

            if (status == BluetoothGatt.GATT_SUCCESS) {
                val service = gatt.getService(URSAFE_SERVICE_UUID)
                if (service != null) {
                    updatePeer(peer.copy(connectionState = PeerConnectionState.GATT_READY))
                    performHandshake(gatt, service)
                }
            }
        }
    }

    private fun performHandshake(gatt: BluetoothGatt, service: BluetoothGattService) {
        val address = gatt.device.address
        val peer = _discoveredPeers.value[address] ?: return

        updatePeer(peer.copy(connectionState = PeerConnectionState.HANDSHAKING))

        val handshakeChar = service.getCharacteristic(HANDSHAKE_CHAR_UUID)
        if (handshakeChar != null) {
            val identityJson = """{"deviceId":"$myDeviceId","displayName":"$myName","role":"$myRole","caps":["BLE_DIRECT","LORA_MESH"]}"""
            handshakeChar.value = identityJson.toByteArray(Charsets.UTF_8)
            gatt.writeCharacteristic(handshakeChar)

            val updatedPeer = peer.copy(
                connectionState = PeerConnectionState.READY,
                authState = PeerAuthState.AUTHENTICATED,
                trustState = PeerTrustState.TRUSTED_OFFICIAL
            )
            updatePeer(updatedPeer)
            notificationManager?.showPeerConnectedNotification(updatedPeer.displayName, updatedPeer.role.name)
        }
    }

    fun sendEnvelope(peerAddress: String, envelope: MessageEnvelope): Boolean {
        val gatt = activeGattClients[peerAddress] ?: return false
        val service = gatt.getService(URSAFE_SERVICE_UUID) ?: return false
        val envelopeChar = service.getCharacteristic(ENVELOPE_CHAR_UUID) ?: return false

        val payloadJson = serializeEnvelope(envelope)
        envelopeChar.value = payloadJson.toByteArray(Charsets.UTF_8)
        return gatt.writeCharacteristic(envelopeChar)
    }

    fun broadcastEnvelope(envelope: MessageEnvelope): Int {
        var count = 0
        activeGattClients.forEach { (addr, _) ->
            if (sendEnvelope(addr, envelope)) count++
        }
        return count
    }

    private fun initGattServer() {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager ?: return
        gattServer = manager.openGattServer(context, object : BluetoothGattServerCallback() {
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
                if (responseNeeded) {
                    gattServer?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null)
                }
                handleServerReceivedWrite(device.address, characteristic.uuid, payloadString)
            }
        })

        val service = BluetoothGattService(URSAFE_SERVICE_UUID, BluetoothGattService.SERVICE_TYPE_PRIMARY)
        val identityChar = BluetoothGattCharacteristic(IDENTITY_CHAR_UUID, BluetoothGattCharacteristic.PROPERTY_READ or BluetoothGattCharacteristic.PROPERTY_WRITE, BluetoothGattCharacteristic.PERMISSION_READ or BluetoothGattCharacteristic.PERMISSION_WRITE)
        val handshakeChar = BluetoothGattCharacteristic(HANDSHAKE_CHAR_UUID, BluetoothGattCharacteristic.PROPERTY_WRITE, BluetoothGattCharacteristic.PERMISSION_WRITE)
        val envelopeChar = BluetoothGattCharacteristic(ENVELOPE_CHAR_UUID, BluetoothGattCharacteristic.PROPERTY_WRITE, BluetoothGattCharacteristic.PERMISSION_WRITE)
        val ackChar = BluetoothGattCharacteristic(ACK_CHAR_UUID, BluetoothGattCharacteristic.PROPERTY_WRITE, BluetoothGattCharacteristic.PERMISSION_WRITE)

        service.addCharacteristic(identityChar)
        service.addCharacteristic(handshakeChar)
        service.addCharacteristic(envelopeChar)
        service.addCharacteristic(ackChar)

        gattServer?.addService(service)
    }

    private fun startAdvertising() {
        val advertiser = bluetoothLeAdvertiser ?: return
        val settings = AdvertiseSettings.Builder().setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY).setConnectable(true).build()
        val data = AdvertiseData.Builder().setIncludeDeviceName(true).addServiceUuid(ParcelUuid(URSAFE_SERVICE_UUID)).build()
        try {
            advertiser.startAdvertising(settings, data, object : AdvertiseCallback() {})
        } catch (e: Exception) {
            Log.e(TAG, "[BLE] Advertising error: ${e.message}")
        }
    }

    private fun handleServerReceivedWrite(senderAddress: String, uuid: UUID, payload: String) {
        when (uuid) {
            ENVELOPE_CHAR_UUID -> {
                val envelope = parseEnvelope(payload)
                if (envelope != null) {
                    onEnvelopeReceivedListener?.invoke(envelope)
                    sendAck(senderAddress, envelope.messageId)
                }
            }
            ACK_CHAR_UUID -> {
                onAckReceivedListener?.invoke(payload, senderAddress)
            }
        }
    }

    private fun sendAck(peerAddress: String, messageId: String) {
        scope.launch {
            val gatt = activeGattClients[peerAddress] ?: return@launch
            val service = gatt.getService(URSAFE_SERVICE_UUID) ?: return@launch
            val ackChar = service.getCharacteristic(ACK_CHAR_UUID) ?: return@launch
            ackChar.value = messageId.toByteArray(Charsets.UTF_8)
            gatt.writeCharacteristic(ackChar)
        }
    }

    private fun updatePeer(peer: UrSafePeer) {
        val map = _discoveredPeers.value.toMutableMap()
        map[peer.bluetoothAddress] = peer
        _discoveredPeers.value = map
    }

    private fun serializeEnvelope(envelope: MessageEnvelope): String {
        return """{"messageId":"${envelope.messageId}","senderId":"${envelope.senderId}","senderRole":"${envelope.senderRole.name}","senderName":"${envelope.senderName}","recipientId":"${envelope.recipientId}","messageType":"${envelope.messageType}","priority":${envelope.priority.code},"createdAtEpochMs":${envelope.createdAtEpochMs},"payloadJson":${quote(envelope.payloadJson)},"payloadHash":"${envelope.payloadHash}"}"""
    }

    private fun parseEnvelope(json: String): MessageEnvelope? {
        return try {
            val id = extractJsonVal(json, "messageId") ?: return null
            val sender = extractJsonVal(json, "senderId") ?: "unknown"
            val senderName = extractJsonVal(json, "senderName") ?: "UrSafe User"
            val type = extractJsonVal(json, "messageType") ?: "MSG"
            val prio = extractJsonInt(json, "priority") ?: 0
            val payload = extractJsonVal(json, "payloadJson") ?: ""
            val hash = extractJsonVal(json, "payloadHash") ?: ""

            MessageEnvelope(
                messageId = id,
                senderId = sender,
                senderName = senderName,
                messageType = type,
                priority = Priority.fromCode(prio),
                payloadJson = payload,
                payloadHash = hash,
                deliveryState = DeliveryState.RECEIVED
            )
        } catch (e: Exception) {
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
}
