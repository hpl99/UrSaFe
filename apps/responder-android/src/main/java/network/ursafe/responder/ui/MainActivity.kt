package network.ursafe.responder.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Share
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import network.ursafe.responder.core.model.PeerConnectionState
import network.ursafe.responder.core.model.UrSafePeer
import network.ursafe.responder.core.model.UserRole

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colors = darkColors(
                    primary = Color(0xFF00E676),
                    primaryVariant = Color(0xFF00C853),
                    secondary = Color(0xFF2979FF),
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
                    ResponderMainAppScreen()
                }
            }
        }
    }
}

@Composable
fun ResponderMainAppScreen() {
    var selectedTab by remember { mutableStateOf(0) }

    Column(modifier = Modifier.fillMaxSize()) {
        TabRow(
            selectedTabIndex = selectedTab,
            backgroundColor = Color(0xFF121824),
            contentColor = Color(0xFF00E676)
        ) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("🛡️ TACTICAL MISSION", fontWeight = FontWeight.Bold) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("📡 CONNECTIVITY MESH", fontWeight = FontWeight.Bold) }
            )
        }

        when (selectedTab) {
            0 -> ResponderTacticalScreen()
            1 -> ResponderConnectivityMeshScreen()
        }
    }
}

@Composable
fun ResponderTacticalScreen() {
    var missionState by remember { mutableStateOf("ASSIGNED") }
    var evidenceHash by remember { mutableStateOf<String?>(null) }
    var reportSubmitted by remember { mutableStateOf(false) }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = "URSAFE RESPONDER", fontWeight = FontWeight.Bold, fontSize = 20.sp, color = Color.White)
                Text(text = "Capt. Vikram Singh (NDRF-B-108)", fontSize = 12.sp, color = Color(0xFF9DB0D1))
            }
            Surface(color = Color(0xFF00E676).copy(alpha = 0.15f), shape = RoundedCornerShape(16.dp)) {
                Text(text = "ROLE: RESPONDER", modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp), fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color(0xFF00E676))
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(text = "VERIFIED CREDENTIAL & RADIO LINK", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
                Spacer(modifier = Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "W3C Passport:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "VALID (NDRF / SDMA)", color = Color(0xFF00E676), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Radio Device:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "URSAFE-RADIO-01 (Heltec V3)", color = Color(0xFF00E5FF), fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = "Mesh Transport:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "LoRa 865 MHz (3 nodes reachable)", color = Color.White, fontSize = 13.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "INCIDENT #UR-2026-001", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 15.sp)
                    Surface(color = Color(0xFFFF334B).copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp)) {
                        Text(text = "CRITICAL FLOOD", modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color(0xFFFF334B))
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text(text = "Victim: Priya Sharma (2 trapped in rising water)", fontSize = 13.sp, color = Color.White)
                Text(text = "Location: Milan Subway, Santacruz (19.0760° N, 72.8777° E)", fontSize = 12.sp, color = Color(0xFF9DB0D1))
                Text(text = "Distance: ~1.2 km • ETA: 6 mins", fontSize = 12.sp, color = Color(0xFF00E5FF))

                Spacer(modifier = Modifier.height(14.dp))

                Text(text = "MISSION ACTION STATE: $missionState", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { missionState = "ACCEPTED" },
                        colors = ButtonDefaults.buttonColors(backgroundColor = if (missionState == "ACCEPTED") Color(0xFF2979FF) else Color(0xFF121824)),
                        modifier = Modifier.weight(1f)
                    ) { Text("Accept", fontSize = 11.sp) }

                    Button(
                        onClick = { missionState = "EN_ROUTE" },
                        colors = ButtonDefaults.buttonColors(backgroundColor = if (missionState == "EN_ROUTE") Color(0xFFFF9100) else Color(0xFF121824)),
                        modifier = Modifier.weight(1f)
                    ) { Text("En Route", fontSize = 11.sp) }

                    Button(
                        onClick = { missionState = "ON_SCENE" },
                        colors = ButtonDefaults.buttonColors(backgroundColor = if (missionState == "ON_SCENE") Color(0xFF00E676) else Color(0xFF121824)),
                        modifier = Modifier.weight(1f)
                    ) { Text("On Scene", fontSize = 11.sp) }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(text = "RESCUE PROOF & EVIDENCE SUBMISSION", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color.White)
                Text(text = "Direct closure without verified evidence is strictly prohibited (Section 27).", fontSize = 11.sp, color = Color(0xFF9DB0D1))

                Spacer(modifier = Modifier.height(12.dp))

                if (evidenceHash == null) {
                    Button(
                        onClick = { evidenceHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" },
                        colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF26334D)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Filled.Share, contentDescription = "Camera", tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = "Capture Tactical Photo / Video", color = Color.White, fontSize = 12.sp)
                    }
                } else {
                    Surface(color = Color(0xFF0E1420), shape = RoundedCornerShape(6.dp), modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text(text = "PHOTO ATTACHED: rescue_site_01.jpg", fontSize = 12.sp, color = Color(0xFF00E676))
                            Text(text = "SHA-256: ${evidenceHash?.take(18)}...", fontSize = 11.sp, color = Color(0xFF9DB0D1))
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    if (!reportSubmitted) {
                        Button(
                            onClick = { reportSubmitted = true },
                            colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF00E676)),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Filled.CheckCircle, contentDescription = "Submit", tint = Color.Black)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(text = "SUBMIT RESCUE REPORT TO AUTHORITY", fontWeight = FontWeight.Bold, color = Color.Black, fontSize = 12.sp)
                        }
                    } else {
                        Surface(color = Color(0xFF00E676).copy(alpha = 0.15f), shape = RoundedCornerShape(6.dp), modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = "REPORT SUBMITTED: Awaiting SDMA Authority Co-Sign.",
                                modifier = Modifier.padding(12.dp),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF00E676)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ResponderConnectivityMeshScreen() {
    var isScanning by remember { mutableStateOf(false) }
    var testStatusText by remember { mutableStateOf<String?>(null) }

    val samplePeers = listOf(
        UrSafePeer("p-01", "48:1A:89:FE:26:01", "Priya Sharma (Victim)", UserRole.CITIZEN, PeerConnectionState.READY, rssiDbm = -55, batteryPercent = 88),
        UrSafePeer("p-02", "48:1A:89:FE:26:02", "Capt. Vikram (Self)", UserRole.RESPONDER, PeerConnectionState.CONNECTED, rssiDbm = -45, batteryPercent = 98)
    )

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Responder Mesh (0xFE26)", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = Color.White)
                Text("Bluetooth: ON • Service 0xFE26 GATT", fontSize = 12.sp, color = Color(0xFF00E676))
            }

            Button(
                onClick = { isScanning = !isScanning },
                colors = ButtonDefaults.buttonColors(backgroundColor = if (isScanning) Color(0xFFFF9100) else Color(0xFF00E676))
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = "Scan", tint = Color.Black)
                Spacer(modifier = Modifier.width(4.dp))
                Text(if (isScanning) "Scanning..." else "Scan BLE", color = Color.Black, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text("Discovered Field Peers", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
        Spacer(modifier = Modifier.height(8.dp))

        samplePeers.forEach { peer ->
            Card(
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
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
                            Text(text = "🟢", fontSize = 12.sp)
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(text = peer.displayName, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                        }
                        Text(text = "${peer.rssiDbm} dBm", fontSize = 11.sp, color = Color(0xFF9DB0D1))
                    }

                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(text = "State: ${peer.connectionState.name}", fontSize = 11.sp, color = Color(0xFF00E5FF))
                        Text(text = "Battery: ${peer.batteryPercent}%", fontSize = 11.sp, color = Color(0xFF9DB0D1))
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = { testStatusText = "Responder Handshake & W3C Passport Verified for ${peer.displayName}." },
                            colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF26334D)),
                            modifier = Modifier.weight(1f)
                        ) { Text("Verify W3C", fontSize = 10.sp, color = Color.White) }

                        Button(
                            onClick = { testStatusText = "Tactical ACK sent to ${peer.displayName} over BLE (0xFE26)." },
                            colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF00E676)),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.Send, contentDescription = "Send", tint = Color.Black, modifier = Modifier.size(12.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Send ACK", fontSize = 10.sp, color = Color.Black, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        Text("Physical Radio Interface (LoRa)", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF627494))
        Spacer(modifier = Modifier.height(8.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("URSAFE-RADIO-01", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
                    Surface(color = Color(0xFF00E676).copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp)) {
                        Text("CONNECTED", modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), fontSize = 10.sp, color = Color(0xFF00E676), fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text("Hardware: Heltec V3 Transceiver (865 MHz IN)", fontSize = 12.sp, color = Color(0xFF9DB0D1))
                Text("Node ID: !3b2a1c90 • Band: 865.2 MHz", fontSize = 12.sp, color = Color(0xFF00E5FF))
                Text("Battery: 98% • Signal: -62 dBm (SNR 9.8dB)", fontSize = 12.sp, color = Color.White)
                Text("Reachable Tactical Nodes: 6 active nodes", fontSize = 12.sp, color = Color(0xFF9DB0D1))
            }
        }

        if (testStatusText != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Surface(color = Color(0xFF00E676).copy(alpha = 0.15f), shape = RoundedCornerShape(6.dp), modifier = Modifier.fillMaxWidth()) {
                Text(text = testStatusText!!, modifier = Modifier.padding(12.dp), fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF00E676))
            }
        }
    }
}
