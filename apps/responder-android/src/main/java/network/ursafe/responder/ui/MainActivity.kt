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
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Share
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

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
                    ResponderTacticalScreen()
                }
            }
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
        // Top Header & Identity Badge
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "URSAFE RESPONDER",
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = Color.White
                )
                Text(
                    text = "Capt. Vikram Singh (NDRF-B-108)",
                    fontSize = 12.sp,
                    color = Color(0xFF9DB0D1)
                )
            }
            Surface(
                color = Color(0xFF00E676).copy(alpha = 0.15f),
                shape = RoundedCornerShape(16.dp)
            ) {
                Text(
                    text = "ROLE: RESPONDER",
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF00E676)
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Hardware & Credential Status Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "VERIFIED CREDENTIAL & RADIO LINK",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF627494)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "W3C Passport:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "VALID (NDRF / SDMA)", color = Color(0xFF00E676), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Radio Device:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "URSAFE-RADIO-01 (Heltec V3)", color = Color(0xFF00E5FF), fontSize = 13.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Mesh Transport:", color = Color(0xFF9DB0D1), fontSize = 13.sp)
                    Text(text = "LoRa 865 MHz (3 nodes reachable)", color = Color.White, fontSize = 13.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Active Mission Card
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
                        text = "INCIDENT #UR-2026-001",
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        fontSize = 15.sp
                    )
                    Surface(
                        color = Color(0xFFFF334B).copy(alpha = 0.2f),
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Text(
                            text = "CRITICAL FLOOD",
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFFF334B)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Victim: Priya Sharma (2 trapped in rising water)",
                    fontSize = 13.sp,
                    color = Color.White
                )
                Text(
                    text = "Location: Milan Subway, Santacruz (19.0760° N, 72.8777° E)",
                    fontSize = 12.sp,
                    color = Color(0xFF9DB0D1)
                )
                Text(
                    text = "Distance: ~1.2 km • ETA: 6 mins",
                    fontSize = 12.sp,
                    color = Color(0xFF00E5FF)
                )

                Spacer(modifier = Modifier.height(14.dp))

                // Tactical Mission Progression Buttons
                Text(
                    text = "MISSION ACTION STATE: $missionState",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF627494)
                )
                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Button(
                        onClick = { missionState = "ACCEPTED" },
                        colors = ButtonDefaults.buttonColors(
                            backgroundColor = if (missionState == "ACCEPTED") Color(0xFF2979FF) else Color(0xFF121824)
                        ),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Accept", fontSize = 11.sp)
                    }

                    Button(
                        onClick = { missionState = "EN_ROUTE" },
                        colors = ButtonDefaults.buttonColors(
                            backgroundColor = if (missionState == "EN_ROUTE") Color(0xFFFF9100) else Color(0xFF121824)
                        ),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("En Route", fontSize = 11.sp)
                    }

                    Button(
                        onClick = { missionState = "ON_SCENE" },
                        colors = ButtonDefaults.buttonColors(
                            backgroundColor = if (missionState == "ON_SCENE") Color(0xFF00E676) else Color(0xFF121824)
                        ),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("On Scene", fontSize = 11.sp)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Cryptographic Evidence & Rescue Report Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = Color(0xFF182030),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "RESCUE PROOF & EVIDENCE SUBMISSION",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "Direct closure without verified evidence is strictly prohibited (Section 27).",
                    fontSize = 11.sp,
                    color = Color(0xFF9DB0D1)
                )

                Spacer(modifier = Modifier.height(12.dp))

                if (evidenceHash == null) {
                    Button(
                        onClick = {
                            evidenceHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                        },
                        colors = ButtonDefaults.buttonColors(backgroundColor = Color(0xFF26334D)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Filled.Share, contentDescription = "Camera", tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = "Capture Tactical Photo / Video", color = Color.White, fontSize = 12.sp)
                    }
                } else {
                    Surface(
                        color = Color(0xFF0E1420),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text(text = "PHOTO ATTACHED: rescue_site_01.jpg", fontSize = 12.sp, color = Color(0xFF00E676))
                            Text(
                                text = "SHA-256: ${evidenceHash?.take(18)}...",
                                fontSize = 11.sp,
                                color = Color(0xFF9DB0D1)
                            )
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
                        Surface(
                            color = Color(0xFF00E676).copy(alpha = 0.15f),
                            shape = RoundedCornerShape(6.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
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
