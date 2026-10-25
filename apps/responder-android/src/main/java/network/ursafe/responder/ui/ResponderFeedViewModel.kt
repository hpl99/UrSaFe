package network.ursafe.responder.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import network.ursafe.responder.data.local.IncidentDao
import network.ursafe.responder.data.local.IncidentEntity
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class ResponderFeedViewModel(private val dao: IncidentDao) : ViewModel() {
    val incidentsFlow: StateFlow<List<IncidentEntity>> = dao.getActiveIncidentsFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun acceptIncident(incidentId: String) {
        viewModelScope.launch {
            dao.updateStatus(incidentId, "ACCEPTED")
            // Triggers Meshtastic LoRa ACK packet broadcast
        }
    }

    fun markArrived(incidentId: String) {
        viewModelScope.launch {
            dao.updateStatus(incidentId, "ARRIVED")
        }
    }

    fun completeRescue(incidentId: String) {
        viewModelScope.launch {
            dao.updateStatus(incidentId, "COMPLETED")
            // Triggers dual-confirmed Rescue Receipt generation
        }
    }

    fun declineIncident(incidentId: String) {
        viewModelScope.launch {
            dao.updateStatus(incidentId, "DECLINED")
        }
    }
}
