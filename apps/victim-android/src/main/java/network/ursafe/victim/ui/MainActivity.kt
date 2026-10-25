package network.ursafe.victim.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import network.ursafe.victim.data.local.EmergencyEntity

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
                    CitizenEmergencyScreen()
                }
            }
        }
    }
}

@Composable
fun CitizenEmergencyScreen() {
    var emergencyTriggered by remember { mutableStateOf(false) }
    var selectedCategory by remember { mutableStateOf("FLOOD") }
    var peopleCount by remember { mutableStateOf(1) }
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
                Text(
                    text = "URSAFE SOS",
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = Color.White
                )
                Text(
                    text = "Civilian Life-Safety Beacon",
                    fontSize = 12.sp,
                    color = Color(0xFF9DB0D1)
                )
            }
            Surface(
                color = Color(0xFF1E293B),
                shape = RoundedCornerShape(16.dp)
            ) {
                Text(
                    text = "ROLE: CITIZEN",
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFFF9100)
                )
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
                Text(
                    text = "HARDWARE & MESH LINK",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF627494)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Radio Link:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "● CONNECTED (Heltec V3)", color = Color(0xFF00E676), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Hardware GNSS:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "19.0760° N, 72.8777° E (±4m)", color = Color(0xFF00E5FF), fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Offline Outbox:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "0 PENDING (Local SQLite WAL)", color = Color.White, fontSize = 13.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        if (!emergencyTriggered) {
            // SOS Trigger Interface
            Card(
                modifier = Modifier.fillMaxWidth(),
                backgroundColor = Color(0xFF182030),
                elevation = 6.dp,
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "DECLARE EMERGENCY",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Text(
                        text = "100% offline-first. Broadcasts directly over LoRa RF mesh.",
                        fontSize = 12.sp,
                        color = Color(0xFF9DB0D1)
                    )
                    Spacer(modifier = Modifier.height(14.dp))

                    Text(text = "Category: $selectedCategory", fontSize = 13.sp, color = Color.White)
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = { selectedCategory = "FLOOD" },
                            colors = ButtonDefaults.buttonColors(backgroundColor = if (selectedCategory == "FLOOD") Color(0xFF2979FF) else Color(0xFF121824)),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(text = "Flood", fontSize = 11.sp)
                        }
                        Button(
                            onClick = { selectedCategory = "MEDICAL" },
                            colors = ButtonDefaults.buttonColors(backgroundColor = if (selectedCategory == "MEDICAL") Color(0xFFFF334B) else Color(0xFF121824)),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(text = "Medical", fontSize = 11.sp)
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = victimNotes,
                        onValueChange = { victimNotes = it },
                        label = { Text("Details (e.g. 2nd floor, water rising)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = TextFieldDefaults.outlinedTextFieldColors(
                            textColor = Color.White,
                            focusedBorderColor = Color(0xFF2979FF),
                            unfocusedBorderColor = Color(0xFF26334D)
                        )
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    Button(
                        onClick = {
                            emergencyTriggered = true
                            progressionStatus = "QUEUED_LOCAL"
                        },
                        colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFFFF334B)),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(56.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Icon(Icons.Filled.Warning, contentDescription = "SOS", tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "TRANSMIT EMERGENCY SOS",
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                }
            }
        } else {
            // Active Emergency Status Card & Stepper
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
                        Text(
                            text = "ACTIVE SOS BEACON",
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFFF334B)
                        )
                        Surface(
                            color = Color(0xFF2979FF).copy(alpha = 0.2f),
                            shape = RoundedCornerShape(4.dp)
                        ) {
                            Text(
                                text = progressionStatus,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF00E5FF)
                            )
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
