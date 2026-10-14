package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import rewatch.c900.CommandQueue
import rewatch.c900.FrameReader
import rewatch.c900.Frames
import rewatch.c900.Gatt
import rewatch.c900.HealthSync
import rewatch.c900.Session

/**
 * End-to-end JVM consistency test.
 *
 * Drives WatchService logic (Session + CommandQueue + PacingScheduler + HealthSync)
 * against a simulated watch (SimWatch) through a fake GATT link.
 *
 * Flow:
 * 1. Connect and service discovery (Gatt.COMMAND_SERVICE, write/notify characteristics).
 * 2. 4 Info reads: HW revision (0x2A27 -> 0x10), SW revision (0x2A26), Features (0x2A28), Battery (0x2A19).
 * 3. Notification enabled on command notify characteristic -> Session enters READY.
 * 4. Message command submitted through CommandQueue, paced across ATT pieces via PacingScheduler.
 * 5. SimWatch receives full message and returns protocol ACK -> CommandQueue resolves Ok.
 * 6. Inbound Cmd 5 health sync sequence:
 *    - Key 7: sync start marker -> HealthSync enters SYNCING.
 *    - Key 12: day totals record (steps, distance, calories).
 *    - Key 8: sync end marker -> HealthSync enters DONE.
 *
 * NOTE: This test proves protocol and architecture consistency only, never hardware truth (ground rule 6).
 */
class EndToEndTest {

    /**
     * Simulated watch for tests (mirroring core's SimWatch):
     * proves consistency only, never hardware truth (ground rule 6).
     */
    class SimWatch(val ver: Int = Frames.C900_VER) {
        private val reader = FrameReader()
        val received = mutableListOf<Frames.Inbound.Cmd>()
        var notifyEnabled = false
        var lastAckSent: ByteArray? = null

        fun write(piece: ByteArray, onNotify: (ByteArray) -> Unit) {
            val frames = reader.feed(piece)
            for (f in frames) {
                if (f is Frames.Inbound.Cmd) {
                    received.add(f)
                    val ack = Frames.ack(f.cmd, f.key, x = 9 + f.payload.size, status = 1) // I-18 [H]
                    lastAckSent = ack
                    if (notifyEnabled) {
                        onNotify(ack)
                    }
                }
            }
        }
    }

    /**
     * Fake link connecting Session, CommandQueue, PacingScheduler, HealthSync, and SimWatch.
     */
    class FakeGattLink(
        val simWatch: SimWatch,
        val session: Session,
        val healthSync: HealthSync,
        private val nowMs: () -> Long
    ) {
        var notifyEnabled = false
        val reader = FrameReader()
        var completedResults = mutableListOf<CommandQueue.Result>()

        lateinit var pacingScheduler: PacingScheduler
        lateinit var commandQueue: CommandQueue

        fun initQueueAndScheduler(postDelayedRunner: (Long, () -> Unit) -> Unit) {
            pacingScheduler = PacingScheduler(
                execute = { op -> executeGattOp(op) },
                postDelayed = postDelayedRunner,
                nowMs = nowMs
            )
            commandQueue = CommandQueue(
                write = { piece -> pacingScheduler.enqueue(GattOp.WritePiece(piece)) },
                nowMs = nowMs
            )
        }

        fun executeGattOp(op: GattOp) {
            when (op) {
                is GattOp.Read -> {
                    val value = readSimChar(op.uuid)
                    pacingScheduler.onComplete(op)
                    val actions = session.readResult(op.uuid, value)
                    actions.forEach { dispatchSessionAction(it) }
                }
                is GattOp.EnableNotify -> {
                    notifyEnabled = true
                    simWatch.notifyEnabled = true
                    pacingScheduler.onComplete(op)
                }
                is GattOp.WritePiece -> {
                    simWatch.write(op.piece) { inboundNotifyBytes ->
                        feedNotifyBytes(inboundNotifyBytes)
                    }
                    pacingScheduler.onComplete(op)
                }
            }
        }

        private fun readSimChar(uuid: String): ByteArray? {
            val short = uuid.lowercase().replace("-", "").removePrefix("0000").substring(0, 4)
            return when (short) {
                "2a27" -> "10000".toByteArray() // HW rev -> 0x10 [H]
                "2a26" -> "C900".toByteArray()
                "2a28" -> byteArrayOf(0xAA.toByte(), 0xCF.toByte(), 0xE0.toByte(), 0x81.toByte(), 0xDF.toByte())
                "2a19" -> byteArrayOf(85) // Battery 85%
                else -> null
            }
        }

        fun dispatchSessionAction(action: Session.Action) {
            when (action) {
                is Session.Action.Read -> pacingScheduler.enqueue(GattOp.Read(action.uuid))
                is Session.Action.EnableNotify -> pacingScheduler.enqueue(GattOp.EnableNotify)
                is Session.Action.Ack -> {
                    Gatt.pieces(action.bytes).forEach { piece ->
                        pacingScheduler.enqueue(GattOp.WritePiece(piece))
                    }
                }
                is Session.Action.AskUserBond -> { /* user bond prompt */ }
                is Session.Action.Fail -> { /* terminal failure */ }
            }
        }

        fun feedNotifyBytes(bytes: ByteArray) {
            val frames = reader.feed(bytes)
            for (f in frames) {
                when (f) {
                    is Frames.Inbound.Ack -> commandQueue.onAck(f)
                    is Frames.Inbound.Cmd -> {
                        healthSync.onCommand(f)
                        val actions = session.onCommand(f, f.payload.size + 9)
                        actions.forEach { dispatchSessionAction(it) }
                    }
                    is Frames.Inbound.Bad -> { }
                }
            }
        }
    }

    private fun buildSimInboundFrame(cmd: Int, key: Int, payload: ByteArray = ByteArray(0), ver: Int = 1): ByteArray {
        val total = 9 + payload.size
        val n = total - 4
        val f = ByteArray(total)
        f[0] = Frames.APP_HEADER.toByte()
        f[1] = (n shr 8).toByte()
        f[2] = n.toByte()
        f[4] = cmd.toByte()
        f[5] = ver.toByte()
        f[6] = key.toByte()
        f[7] = (payload.size shr 8).toByte()
        f[8] = payload.size.toByte()
        payload.copyInto(f, 9)
        f[3] = Frames.checksum(f).toByte()
        return f
    }

    @Test
    fun testEndToEndSessionWithSimWatch() {
        var simulatedTime = 1000L
        val clock = { simulatedTime }

        val simWatch = SimWatch()
        val session = Session()
        val healthSync = HealthSync(nowMs = clock)
        val fakeLink = FakeGattLink(simWatch, session, healthSync, clock)

        fakeLink.initQueueAndScheduler { delayMs, task ->
            simulatedTime += delayMs
            task()
        }

        // 1. Connect
        session.connecting()
        assertEquals(Session.State.CONNECTING, session.state)

        // Services discovered: Command service + characteristics
        val serviceUuids = listOf(
            Gatt.COMMAND_SERVICE,
            "0000180a-0000-1000-8000-00805f9b34fb",
            "0000180f-0000-1000-8000-00805f9b34fb"
        )
        val commandChars = listOf(Gatt.COMMAND_WRITE, Gatt.COMMAND_NOTIFY)
        val discoveryActions = session.discovered(serviceUuids, commandChars)
        assertEquals(4, discoveryActions.size) // 4 reads queued
        discoveryActions.forEach { fakeLink.dispatchSessionAction(it) }

        // 2 & 3. 4 reads and EnableNotify should have completed through PacingScheduler
        assertEquals(Session.State.READY, session.state)
        assertEquals(0x10, session.ver)
        assertEquals(85, session.battery)
        assertTrue(fakeLink.notifyEnabled)
        assertTrue(simWatch.notifyEnabled)

        // 4. One message command submitted through CommandQueue
        val messageCmd = session.commands().message(
            type = NotificationMapper.TYPE_SMS,
            title = "Test SMS",
            body = "End-to-end JVM verification message"
        )
        var messageAckResult: CommandQueue.Result? = null
        fakeLink.commandQueue.submit(messageCmd) { result ->
            messageAckResult = result
        }

        // 5. Message pieces executed via PacingScheduler, SimWatch reassembled and ACKed
        assertNotNull(messageAckResult)
        assertTrue(messageAckResult is CommandQueue.Result.Ok)
        val okResult = messageAckResult as CommandQueue.Result.Ok
        assertEquals(0x02, okResult.cmd)
        assertEquals(0x12, okResult.key) // key 18 = message push
        assertFalse(fakeLink.commandQueue.busy)
        assertEquals(1, simWatch.received.size)
        assertEquals(0x02, simWatch.received[0].cmd)
        assertEquals(0x12, simWatch.received[0].key)

        // 6. Inbound Cmd 5 health sync 7..12..8
        // Start marker (key 7)
        val syncStartFrame = buildSimInboundFrame(cmd = 5, key = 7)
        fakeLink.feedNotifyBytes(syncStartFrame)
        assertEquals(HealthSync.State.SYNCING, healthSync.state)

        // Day total (key 12): steps = 8000, distance = 5600 m (5.60 km), calories = 240000 cal (240.00 kcal)
        // 8000 = 0x00001F40, 5600 = 0x000015E0, 240000 = 0x0003A980
        val dayTotalPayload = byteArrayOf(
            0x00, 0x00, 0x1F, 0x40.toByte(), // steps: 8000
            0x00, 0x00, 0x15, 0xE0.toByte(), // distanceM: 5600
            0x00, 0x03, 0xA9.toByte(), 0x80.toByte() // calorieCal: 240000
        )
        val dayTotalFrame = buildSimInboundFrame(cmd = 5, key = 12, payload = dayTotalPayload)
        fakeLink.feedNotifyBytes(dayTotalFrame)
        assertEquals(HealthSync.State.SYNCING, healthSync.state)

        // End marker (key 8)
        val syncEndFrame = buildSimInboundFrame(cmd = 5, key = 8)
        fakeLink.feedNotifyBytes(syncEndFrame)
        assertEquals(HealthSync.State.DONE, healthSync.state)

        // Verify day totals decoded correctly
        val totals = healthSync.dayTotal
        assertNotNull(totals)
        assertEquals(8000L, totals!!.steps)
        assertEquals(5600L, totals.distanceM)
        assertEquals(240000L, totals.calorieCal)
        assertEquals(5.60, totals.km, 1e-4)
        assertEquals(240.0, totals.kcal, 1e-4)

        // Status snapshot reflects the entire end-to-end state
        val snapshot = StatusSnapshot.format(session, healthSync, fakeLink.commandQueue)
        assertEquals("Connected (Ready)", snapshot.connectionState)
        assertEquals("85%", snapshot.battery)
        assertEquals("0x10", snapshot.version)
        assertEquals("5.60 km", snapshot.distanceKm)
        assertEquals("240.00 kcal", snapshot.caloriesKcal)
        assertTrue(snapshot.writesBudget.endsWith("/ 200"))
    }
}
