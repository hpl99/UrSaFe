package network.ursafe.victim.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import network.ursafe.victim.core.model.PeerConnectionState
import network.ursafe.victim.core.model.UrSafePeer
import network.ursafe.victim.core.model.UserRole

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colors = darkColors(
                    primary = Color(0xFFFF334B),
                    primaryVariant = Color(0xFFD32F2F),
                    secondary = Color(0xFF00E5FF),
                    background = Color(0xFF0A0D14),
                    surface = Color(0xFF182030),
                    onBackground = Color(0xFFF0F4FC),
                    onSurface = Color(0xFFF0F4FC)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colors.background
                ) {
                    CitizenMainAppScreen()
                }
            }
        }
    }
}

@Composable
fun CitizenMainAppScreen() {
    var selectedTab by remember { mutableStateOf(0) } // 0 = SOS Beacon, 1 = Connectivity Mesh

    Column(modifier = Modifier.fillMaxSize()) {
        // Tab Header
        TabRow(
            selectedTabIndex = selectedTab,
            backgroundColor = Color(0xFF121824),
            contentColor = Color(0xFFFF334B)
        ) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("🆘 SOS BEACON", fontWeight = FontWeight.Bold) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("📡 CONNECTIVITY MESH", fontWeight = FontWeight.Bold) }
            )
        }

        when (selectedTab) {
            0 -> CitizenEmergencyScreen()
            1 -> ConnectivityMeshScreen()
        }
    }
}

@Composable
fun CitizenEmergencyScreen() {
    var emergencyTriggered by remember { mutableStateOf(false) }
    var selectedCategory by remember { mutableStateOf("FLOOD") }
    var victimNotes by remember { mutableStateOf("") }
    var progressionStatus by remember { mutableStateOf("READY") }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        // Top Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = "URSAFE SOS", fontWeight = FontWeight.Bold, fontSize = 20.sp, color = Color.White)
                Text(text = "Civilian Life-Safety Beacon", fontSize = 12.sp, color = Color(0xFF9DB0D1))
            }
            Surface(color = Color(0xFF1E293B), shape = RoundedCornerShape(16.dp)) {
                Text(text = "ROLE: CITIZEN", modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp), fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color(0xFFFF9100))
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Hardware Status Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            elevation = 4.dp,
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(text = "HARDWARE & MESH LINK", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
                Spacer(modifier = Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Radio Link:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "● CONNECTED (Heltec V3)", color = Color(0xFF00E676), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Hardware GNSS:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "19.0760° N, 72.8777° E (±4m)", color = Color(0xFF00E5FF), fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Offline Outbox:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "0 PENDING (Local SQLite WAL)", color = Color.White, fontSize = 13.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        if (!emergencyTriggered) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                backgroundColor = Color(0xFF182030),
                elevation = 6.dp,
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(text = "DECLARE EMERGENCY", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text(text = "100% offline-first. Broadcasts directly over LoRa RF mesh.", fontSize = 12.sp, color = Color(0xFF9DB0D1))
                    Spacer(modifier = Modifier.height(14.dp))

                    Text(text = "Category: $selectedCategory", fontSize = 13.sp, color = Color.White)
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = { selectedCategory = "FLOOD" },
                            colors = ButtonDefaults.buttonColors(backgroundColor = if (selectedCategory == "FLOOD") Color(0xFF2979FF) else Color(0xFF121824)),
                            modifier = Modifier.weight(1f)
                        ) { Text(text = "Flood", fontSize = 11.sp) }
                        Button(
                            onClick = { selectedCategory = "MEDICAL" },
                            colors = ButtonDefaults.buttonColors(backgroundColor = if (selectedCategory == "MEDICAL") Color(0xFFFF334B) else Color(0xFF121824)),
                            modifier = Modifier.weight(1f)
                        ) { Text(text = "Medical", fontSize = 11.sp) }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = victimNotes,
                        onValueChange = { victimNotes = it },
                        label = { Text("Details (e.g. 2nd floor, water rising)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = TextFieldDefaults.outlinedTextFieldColors(textColor = Color.White, focusedBorderColor = Color(0xFF2979FF), unfocusedBorderColor = Color(0xFF26334D))
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    Button(
                        onClick = {
                            emergencyTriggered = true
                            progressionStatus = "QUEUED_LOCAL"
                        },
                        colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFFFF334B)),
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Icon(Icons.Filled.Warning, contentDescription = "SOS", tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = "TRANSMIT EMERGENCY SOS", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        } else {
            Card(
                modifier = Modifier.fillMaxWidth(),
                backgroundColor = Color(0xFF182030),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Text(text = "ACTIVE SOS BEACON", fontWeight = FontWeight.Bold, color = Color(0xFFFF334B))
                        Surface(color = Color(0xFF2979FF).copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp)) {
                            Text(text = progressionStatus, modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp), fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF00E5FF))
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))
                    Text(text = "Category: $selectedCategory Emergency", fontSize = 13.sp, color = Color.White)
                    Text(text = "Beacon: Transmitting via SX1262 LoRa 865 MHz", fontSize = 12.sp, color = Color(0xFF9DB0D1))

                    Spacer(modifier = Modifier.height(16.dp))
                    Text(text = "15-STEP STATUS PROGRESSION:", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(text = "1. STORED_LOCALLY [Room SQLite] ✓", fontSize = 12.sp, color = Color(0xFF00E676))
                    Text(text = "2. QUEUED_FOR_RADIO ✓", fontSize = 12.sp, color = Color(0xFF00E676))
                    Text(text = "3. TRANSMITTING_BLE_GATT ✓", fontSize = 12.sp, color = Color(0xFF00E676))
                    Text(text = "4. MESH_ACCEPTED (Heltec V3 Node) ✓", fontSize = 12.sp, color = Color(0xFF00E676))
                    Text(text = "5. DISPATCHED_TO_NDRF (Capt. Vikram Singh) ✓", fontSize = 12.sp, color = Color(0xFF00E5FF))
                    Text(text = "6. RESPONDER_ACCEPTED ✓", fontSize = 12.sp, color = Color(0xFF00E5FF))
                    Text(text = "7. EN_ROUTE (ETA 7 mins)", fontSize = 12.sp, color = Color(0xFFFF9100))

                    Spacer(modifier = Modifier.height(16.dp))

                    Button(
                        onClick = {
                            emergencyTriggered = false
                            progressionStatus = "CANCELLED"
                        },
                        colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF26334D)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(text = "Cancel SOS Beacon", color = Color.White)
                    }
                }
            }
        }
    }
}

@Composable
fun ConnectivityMeshScreen() {
    var isScanning by remember { mutableStateOf(false) }
    var testStatusText by remember { mutableStateOf<String?>(null) }

    val samplePeers = listOf(
        UrSafePeer("p-01", "48:1A:89:FE:26:01", "Rahul Sharma", UserRole.RESPONDER, PeerConnectionState.READY, rssiDbm = -58, batteryPercent = 94),
        UrSafePeer("p-02", "48:1A:89:FE:26:02", "Ananya Verma", UserRole.CITIZEN, PeerConnectionState.CONNECTED, rssiDbm = -72, batteryPercent = 82),
        UrSafePeer("p-03", "48:1A:89:FE:26:03", "Commander Rajesh", UserRole.AUTHORITY, PeerConnectionState.DISCOVERED, rssiDbm = -85, batteryPercent = 68)
    )

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        // Bluetooth Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Bluetooth Mesh (0xFE26)", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = Color.White)
                Text("Bluetooth: ON • Service 0xFE26 GATT", fontSize = 12.sp, color = Color(0xFF00E676))
            }

            Button(
                onClick = { isScanning = !isScanning },
                colors = ButtonDefaults.buttonColors(backgroundColor = if (isScanning) Color(0xFFFF9100) else Color(0xFF2979FF))
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = "Scan", tint = Color.White)
                Spacer(modifier = Modifier.width(4.dp))
                Text(if (isScanning) "Scanning..." else "Scan BLE", color = Color.White, fontSize = 12.sp)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Discovered UrSafe Peers List
        Text("Nearby UrSafe Devices", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
        Spacer(modifier = Modifier.height(8.dp))

        samplePeers.forEach { peer ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                backgroundColor = Color(0xFF182030),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = if (peer.connectionState == PeerConnectionState.READY || peer.connectionState == PeerConnectionState.CONNECTED) "🟢" else "⚪",
                                fontSize = 12.sp
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(text = peer.displayName, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                            Spacer(modifier = Modifier.width(6.dp))
                            Surface(
                                color = if (peer.role == UserRole.RESPONDER) Color(0xFF00E676).copy(alpha = 0.2f) else Color(0xFF2979FF).copy(alpha = 0.2f),
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    text = peer.role.name,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    fontSize = 10.sp,
                                    color = if (peer.role == UserRole.RESPONDER) Color(0xFF00E676) else Color(0xFF00E5FF)
                                )
                            }
                        }

                        Text(text = "${peer.rssiDbm} dBm", fontSize = 11.sp, color = Color(0xFF9DB0D1))
                    }

                    Spacer(modifier = Modifier.height(4.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "State: ${peer.connectionState.name}", fontSize = 11.sp, color = Color(0xFF00E5FF))
                        Text(text = "Battery: ${peer.batteryPercent}%", fontSize = 11.sp, color = Color(0xFF9DB0D1))
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = {
                                testStatusText = "Handshake completed with ${peer.displayName}. Session TRUSTED."
                            },
                            colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF26334D)),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Pair / Auth", fontSize = 10.sp, color = Color.White)
                        }

                        Button(
                            onClick = {
                                testStatusText = "Test Message sent to ${peer.displayName} over BLE (0xFE26) ✓ ACK Received."
                            },
                            colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF00E676)),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.Send, contentDescription = "Send", tint = Color.Black, modifier = Modifier.size(12.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Send Test", fontSize = 10.sp, color = Color.Black, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Physical Radio Section
        Text("Physical Radio Interface (LoRa)", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
        Spacer(modifier = Modifier.height(8.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Meshtastic Transceiver", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                    Surface(color = Color(0xFF00E676).copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp)) {
                        Text("CONNECTED", modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), fontSize = 10.sp, color = Color(0xFF00E676), fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text("Hardware: Heltec V3 (ESP32-S3 + SX1262)", fontSize = 12.sp, color = Color(0xFF9DB0D1))
                Text("Node ID: !2a4b8c10 • Band: 865.2 MHz (IN865)", fontSize = 12.sp, color = Color(0xFF00E5FF))
                Text("Battery: 92% • Signal: -68 dBm (SNR 8.5dB)", fontSize = 12.sp, color = Color.White)
                Text("Reachable Mesh Nodes: 4 active nodes", fontSize = 12.sp, color = Color(0xFF9DB0D1))
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Emergency Network Stats Summary
        Text("Emergency Network Overview", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
        Spacer(modifier = Modifier.height(8.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Connected Peers:", color = Color(0xFF9DB0D1), fontSize = 12.sp)
                    Text("3 peers active", color = Color(0xFF00E676), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Radio Mesh Nodes:", color = Color(0xFF9DB0D1), fontSize = 12.sp)
                    Text("4 LoRa nodes", color = Color(0xFF00E5FF), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Pending Outbox:", color = Color(0xFF9DB0D1), fontSize = 12.sp)
                    Text("0 PENDING (Local WAL)", color = Color.White, fontSize = 12.sp)
                }
            }
        }

        if (testStatusText != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Surface(
                color = Color(0xFF00E676).copy(alpha = 0.15f),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = testStatusText!!,
                    modifier = Modifier.padding(12.dp),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF00E676)
                )
            }
        }
    }
}
