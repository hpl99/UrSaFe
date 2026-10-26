package network.ursafe.victim

import network.ursafe.victim.core.model.MessageEnvelope
import network.ursafe.victim.core.model.Priority
import network.ursafe.victim.core.model.UserRole
import org.junit.Assert.*
import org.junit.Test

class MessageEnvelopeTest {

    @Test
    fun testSha256ChecksumCalculation() {
        val payload = """{"emergencyId":"sos-123","category":"FLOOD"}"""
        val hash = MessageEnvelope.sha256Hex(payload)
        assertNotNull(hash)
        assertEquals(64, hash.length) // SHA-256 hex string length
    }

    @Test
    fun testPriorityPreemptionOrdering() {
        val sosPriority = Priority.CRITICAL_SOS.code
        val normalPriority = Priority.NORMAL_MESSAGE.code
        val telemetryPriority = Priority.TELEMETRY.code

        assertTrue("Critical SOS must have lower numerical code for higher preemption priority", sosPriority < normalPriority)
        assertTrue("Normal message must precede telemetry", normalPriority < telemetryPriority)
    }

    @Test
    fun testEnvelopeCreationDefaults() {
        val envelope = MessageEnvelope(
            senderId = "dev-test-01",
            senderRole = UserRole.CITIZEN,
            senderName = "Rahul Sharma",
            messageType = "SOS_CREATED",
            payloadJson = "Emergency flood text"
        )

        assertNotNull(envelope.messageId)
        assertTrue(envelope.messageId.startsWith("msg-"))
        assertEquals(Priority.CRITICAL_SOS, envelope.priority)
        assertEquals(1, envelope.totalChunks)
        assertEquals(0, envelope.chunkIndex)
    }
}
