package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PacingSchedulerTest {

    @Test
    fun testOneOperationInFlightAtATime() {
        val executed = mutableListOf<GattOp>()
        var virtualTime = 1000L
        val scheduler = PacingScheduler(
            execute = { executed.add(it) },
            postDelayed = { _, task -> task() },
            nowMs = { virtualTime }
        )

        val op1 = GattOp.Read("00002a27-0000-1000-8000-00805f9b34fb")
        val op2 = GattOp.Read("00002a26-0000-1000-8000-00805f9b34fb")

        scheduler.enqueue(op1)
        scheduler.enqueue(op2)

        // Only op1 should have executed; op2 waits in queue
        assertEquals(listOf(op1), executed)
        assertTrue(scheduler.isBusy)
        assertEquals(1, scheduler.queuedCount)

        // Complete op1; op2 executes immediately
        scheduler.onComplete(op1)
        assertEquals(listOf(op1, op2), executed)
        assertTrue(scheduler.isBusy)
        assertEquals(0, scheduler.queuedCount)

        scheduler.onComplete(op2)
        assertFalse(scheduler.isBusy)
    }

    @Test
    fun testWritePiecesPaced20MsApart() {
        val executed = mutableListOf<GattOp>()
        val delayedTasks = mutableListOf<Pair<Long, () -> Unit>>()
        var virtualTime = 1000L

        val scheduler = PacingScheduler(
            execute = { executed.add(it) },
            postDelayed = { delay, task -> delayedTasks.add(delay to task) },
            nowMs = { virtualTime },
            pieceGapMs = 20L
        )

        val p1 = GattOp.WritePiece(byteArrayOf(1, 2, 3))
        val p2 = GattOp.WritePiece(byteArrayOf(4, 5, 6))

        scheduler.enqueue(p1)
        scheduler.enqueue(p2)

        // p1 executes immediately
        assertEquals(listOf(p1), executed)
        assertEquals(0, delayedTasks.size)

        // p1 completes after 5 ms (at virtualTime = 1005L)
        virtualTime = 1005L
        scheduler.onComplete(p1)

        // p2 must NOT execute yet; gap of 20 ms required, so delayedTask with delay=15 ms is posted
        assertEquals(listOf(p1), executed)
        assertEquals(1, delayedTasks.size)
        assertEquals(15L, delayedTasks[0].first)

        // Advance virtual time by 15 ms and run task
        virtualTime = 1020L
        delayedTasks[0].second.invoke()

        // p2 has now executed
        assertEquals(listOf(p1, p2), executed)
        scheduler.onComplete(p2)
        assertFalse(scheduler.isBusy)
    }

    @Test
    fun testDeniedUuidsAreNeverQueued() {
        val executed = mutableListOf<GattOp>()
        val scheduler = PacingScheduler(
            execute = { executed.add(it) },
            postDelayed = { _, task -> task() }
        )

        // Denied OTA UUIDs (I-14, I-54)
        val denied1 = GattOp.Read("0000ff00-0000-1000-8000-00805f9b34fb")
        val denied2 = GattOp.Read("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
        val allowed = GattOp.Read("00002a27-0000-1000-8000-00805f9b34fb")

        scheduler.enqueue(denied1)
        scheduler.enqueue(denied2)
        scheduler.enqueue(allowed)

        // Only the allowed operation was enqueued and executed
        assertEquals(listOf(allowed), executed)
    }

    @Test
    fun testClearCancelsInFlightAndQueue() {
        val executed = mutableListOf<GattOp>()
        val scheduler = PacingScheduler(
            execute = { executed.add(it) },
            postDelayed = { _, task -> task() }
        )

        val op1 = GattOp.Read("00002a27-0000-1000-8000-00805f9b34fb")
        val op2 = GattOp.Read("00002a26-0000-1000-8000-00805f9b34fb")

        scheduler.enqueue(op1)
        scheduler.enqueue(op2)
        scheduler.clear()

        assertFalse(scheduler.isBusy)
        assertEquals(0, scheduler.queuedCount)
    }
}
