package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReconnectControllerTest {

    @Test
    fun testNormalReconnectScheduling() {
        var scheduledDelay = -1L
        var scheduledTask: Runnable? = null
        var cancelledCount = 0

        val controller = ReconnectController(
            postDelayed = { delay, r ->
                scheduledDelay = delay
                scheduledTask = r
            },
            removeCallbacks = {
                cancelledCount++
                scheduledTask = null
            }
        )

        controller.onDeviceConnecting(hasDevice = true)
        assertFalse(controller.isFailedTerminal)
        assertFalse(controller.isReconnectScheduled)

        controller.scheduleReconnect(3000L)
        assertTrue(controller.isReconnectScheduled)
        assertEquals(3000L, scheduledDelay)
    }

    @Test
    fun testTerminalFailBlocksReconnect() {
        var scheduledCount = 0
        var cancelledCount = 0

        val controller = ReconnectController(
            postDelayed = { _, _ -> scheduledCount++ },
            removeCallbacks = { cancelledCount++ }
        )

        controller.onDeviceConnecting(hasDevice = true)
        controller.scheduleReconnect(3000L)
        assertEquals(1, scheduledCount)
        assertTrue(controller.isReconnectScheduled)

        // Terminal failure occurs (Session.Action.Fail)
        controller.onTerminalFail()
        assertTrue(controller.isFailedTerminal)
        assertFalse(controller.isReconnectScheduled)

        // Any further reconnect attempts must be blocked
        controller.scheduleReconnect(3000L)
        controller.scheduleReconnect(10000L)
        assertEquals(1, scheduledCount)
        assertFalse(controller.isReconnectScheduled)

        // Only explicitly connecting to a device clears terminal fail
        controller.onDeviceConnecting(hasDevice = true)
        assertFalse(controller.isFailedTerminal)

        controller.scheduleReconnect(3000L)
        assertEquals(2, scheduledCount)
        assertTrue(controller.isReconnectScheduled)
    }

    @Test
    fun testReconnectWithoutDeviceIsIgnored() {
        var scheduledCount = 0
        val controller = ReconnectController(
            postDelayed = { _, _ -> scheduledCount++ },
            removeCallbacks = {}
        )

        controller.scheduleReconnect(3000L)
        assertEquals(0, scheduledCount)
        assertFalse(controller.isReconnectScheduled)
    }
}
