package network.ursafe.responder

import network.ursafe.responder.core.model.MessageEnvelope
import network.ursafe.responder.core.model.Priority
import network.ursafe.responder.core.model.UserRole
import org.junit.Assert.*
import org.junit.Test

class MessageEnvelopeTest {

    @Test
    fun testResponderEnvelopeCreation() {
        val payload = """{"incidentId":"UR-2026-001","action":"ACCEPTED"}"""
        val envelope = MessageEnvelope(
            senderId = "resp-108",
            senderRole = UserRole.RESPONDER,
            senderName = "Capt. Vikram Singh",
            messageType = "SOS_STATUS_UPDATE",
            priority = Priority.RESPONDER_ACK,
            payloadJson = payload
        )

        assertEquals("resp-108", envelope.senderId)
        assertEquals(UserRole.RESPONDER, envelope.senderRole)
        assertEquals(Priority.RESPONDER_ACK, envelope.priority)
        assertEquals(64, envelope.payloadHash.length)
    }
}
