package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Test
import rewatch.c900.CommandQueue
import rewatch.c900.Commands
import rewatch.c900.Frames
import rewatch.c900.Gatt
import rewatch.c900.HealthSync
import rewatch.c900.Session

class StatusSnapshotTest {

    @Test
    fun testNullServiceProducesDefaultSnapshot() {
        val snapshot = StatusSnapshot.from(null)
        assertEquals("Service not running", snapshot.connectionState)
        assertEquals("—", snapshot.battery)
        assertEquals("—", snapshot.version)
        assertEquals("—", snapshot.distanceKm)
        assertEquals("—", snapshot.caloriesKcal)
        assertEquals("0 / 200", snapshot.writesBudget)
    }

    @Test
    fun testFormatsConnectedSessionInfo() {
        val session = Session()
        session.connecting()
        assertEquals("Connecting...", StatusSnapshot.format(session, null, null).connectionState)

        session.discovered(
            listOf(Gatt.COMMAND_SERVICE),
            listOf(Gatt.COMMAND_WRITE, Gatt.COMMAND_NOTIFY)
        )
        // 0x2A27: "10000" -> 0x10
        session.readResult("2a27", "10000".toByteArray())
        session.readResult("2a26", "HW1".toByteArray())
        session.readResult("2a28", byteArrayOf(0xAA.toByte(), 0x01))
        session.readResult("2a19", byteArrayOf(88.toByte())) // 88%

        val snapshot = StatusSnapshot.format(session, null, null)
        assertEquals("Connected (Ready)", snapshot.connectionState)
        assertEquals("88%", snapshot.battery)
        assertEquals("0x10", snapshot.version)
    }

    @Test
    fun testFormatsHealthSyncDayTotals() {
        val healthSync = HealthSync(nowMs = { 1000L })
        // Start sync (key 7)
        healthSync.onCommand(Frames.Inbound.Cmd(cmd = 5, ver = 1, key = 7, payload = byteArrayOf()))

        // Day total (key 12): steps = 5000, distance = 3500 m (3.5 km), calorie = 125000 cal (125.0 kcal)
        // 3500 = 0x00000DAC, 125000 = 0x0001E848, 5000 = 0x00001388
        val payload = byteArrayOf(
            0x00, 0x00, 0x13, 0x88.toByte(), // steps: 5000
            0x00, 0x00, 0x0D, 0xAC.toByte(), // distanceM: 3500
            0x00, 0x01, 0xE8.toByte(), 0x48.toByte() // calorieCal: 125000
        )
        healthSync.onCommand(Frames.Inbound.Cmd(cmd = 5, ver = 1, key = 12, payload = payload))

        val snapshot = StatusSnapshot.format(null, healthSync, null)
        assertEquals("3.50 km", snapshot.distanceKm)
        assertEquals("125.00 kcal", snapshot.caloriesKcal)
    }

    @Test
    fun testFormatsCommandQueueWritesBudget() {
        var writtenPieces = 0
        val queue = CommandQueue(
            write = { writtenPieces++ },
            nowMs = { 1000L },
            maxWritesPerSession = 200
        )

        val cmd = Commands(ver = 0x10).find(on = true)
        queue.submit(cmd) { }

        val snapshot = StatusSnapshot.format(null, null, queue)
        assertEquals("1 / 200", snapshot.writesBudget)
        assertEquals(1, writtenPieces)
    }
}
