package network.ursafe.victim.core.notification

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat

class EmergencyNotificationManager(private val context: Context) {

    companion object {
        const val ALERT_CHANNEL_ID = "ursafe_emergency_alerts"
        const val PEER_CHANNEL_ID = "ursafe_peer_updates"
    }

    init {
        createChannels()
    }

    private fun createChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val alertChannel = NotificationChannel(
                ALERT_CHANNEL_ID,
                "🚨 UrSafe Critical Emergency Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notifies of incoming life-critical SOS alerts over BLE or Meshtastic LoRa"
                enableVibration(true)
            }

            val peerChannel = NotificationChannel(
                PEER_CHANNEL_ID,
                "UrSafe Peer Mesh Connectivity",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifies when nearby UrSafe peers authenticate or establish mesh radio link"
            }

            val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(alertChannel)
            manager.createNotificationChannel(peerChannel)
        }
    }

    fun showEmergencyNotification(title: String, text: String, senderName: String, transport: String, rssi: Int? = null) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val rssiInfo = rssi?.let { " • Signal: ${it}dBm" } ?: ""
        val content = "$text\nReceived via: $transport$rssiInfo"

        val notification = NotificationCompat.Builder(context, ALERT_CHANNEL_ID)
            .setContentTitle("🚨 $title")
            .setContentText(content)
            .setStyle(NotificationCompat.BigTextStyle().bigText(content))
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        manager.notify((System.currentTimeMillis() % 100000).toInt(), notification)
    }

    fun showPeerConnectedNotification(peerName: String, role: String) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = NotificationCompat.Builder(context, PEER_CHANNEL_ID)
            .setContentTitle("🟢 UrSafe Peer Connected")
            .setContentText("Connected & Authenticated with $peerName ($role) over BLE 0xFE26")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        manager.notify((System.currentTimeMillis() % 100000).toInt(), notification)
    }
}
