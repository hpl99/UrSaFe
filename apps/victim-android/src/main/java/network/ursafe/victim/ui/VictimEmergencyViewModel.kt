package network.ursafe.victim.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import network.ursafe.victim.data.local.EmergencyEntity
import network.ursafe.victim.data.repository.EmergencyRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class VictimUiState(
    val activeEmergency: EmergencyEntity? = null,
    val isRadioConnected: Boolean = true,
    val radioBatteryPercent: Int = 92,
    val radioRssi: Int = -72,
    val selectedCategory: String = "FLOOD",
    val selectedUrgency: String = "CRITICAL",
    val peopleCount: Int = 2,
    val descriptionText: String = "",
    val isLoading: Boolean = false,
    val statusMessage: String = "Radio connected. Mesh standing by."
)

class VictimEmergencyViewModel(private val repository: EmergencyRepository) : ViewModel() {
    val activeEmergencyFlow: StateFlow<EmergencyEntity?> = repository.activeEmergency
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    fun triggerOfflineSos(lat: Double, lon: Double, altitude: Float) {
        viewModelScope.launch {
            repository.createOfflineSos(
                category = "FLOOD",
                urgency = "CRITICAL",
                peopleCount = 3,
                lat = lat,
                lon = lon,
                altitude = altitude,
                description = "Rising flood waters, need evacuation immediately",
                signatureHex = "MOCK_HARDWARE_KEYSTORE_ED25519_SIG"
            )
        }
    }

    fun cancelSos(emergencyId: String) {
        viewModelScope.launch {
            repository.cancelEmergency(emergencyId)
        }
    }
}
