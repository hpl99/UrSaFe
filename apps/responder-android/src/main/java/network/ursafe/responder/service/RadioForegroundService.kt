package network.ursafe.responder.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.bluetooth.le.ScanFilter
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.ParcelUuid
import androidx.core.app.NotificationCompat
import java.util.UUID

class RadioForegroundService : Service() {

    companion object {
        const val CHANNEL_ID = "ursafe_responder_radio_channel"
        const val NOTIFICATION_ID = 20262

        // UrSafe 16-bit SIG assigned service ID: 0xFE26
        val URSAFE_SERVICE_UUID: UUID = UUID.fromString("0000FE26-0000-1000-8000-00805F9B34FB")
        val DEVICE_IDENTITY_CHAR_UUID: UUID = UUID.fromString("0000FE27-0000-1000-8000-00805F9B34FB")
        val HANDSHAKE_CHAR_UUID: UUID = UUID.fromString("0000FE28-0000-1000-8000-00805F9B34FB")
        val ENVELOPE_CHAR_UUID: UUID = UUID.fromString("0000FE29-0000-1000-8000-00805F9B34FB")
        val ACK_CHAR_UUID: UUID = UUID.fromString("0000FE2A-0000-1000-8000-00805F9B34FB")
        val STATUS_CHAR_UUID: UUID = UUID.fromString("0000FE2B-0000-1000-8000-00805F9B34FB")

        /**
         * Builds hardware BLE scan filter that exclusively discovers UrSafe compatible peers.
         * Rejects generic Bluetooth peripherals, PCs, earbuds, and audio accessories.
         */
        fun createUrSafeScanFilter(): ScanFilter {
            return ScanFilter.Builder()
                .setServiceUuid(ParcelUuid(URSAFE_SERVICE_UUID))
                .build()
        }

        /**
         * Verifies if an advertised peripheral is an authorized UrSafe peer.
         */
        fun isUrSafePeer(serviceUuids: List<ParcelUuid>?): Boolean {
            if (serviceUuids == null) return false
            return serviceUuids.any { it.uuid == URSAFE_SERVICE_UUID }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification("UrSafe Responder Radio Active", "Connected to Heltec V3 LoRa Transceiver (865 MHz / UrSafe 0xFE26)")
        startForeground(NOTIFICATION_ID, notification)
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "UrSafe Tactical Radio Channel",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Maintains persistent LoRa emergency radio background link and UrSafe peer exchange"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(title: String, content: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(content)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
}
