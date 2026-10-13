package rewatch.c900

import java.io.File
import java.time.LocalDateTime
import kotlin.test.*

private fun hex(b: ByteArray) = b.joinToString("") { "%02x".format(it) }
private fun unhex(s: String) = ByteArray(s.length / 2) { s.substring(it * 2, it * 2 + 2).toInt(16).toByte() }

/** Simulated watch for tests: proves consistency only, never hardware truth (ground rule 6). */
class SimWatch(val ver: Int = Frames.C900_VER) {
    private val reader = FrameReader()
    val received = ArrayList<Frames.Inbound.Cmd>()
    var mute = false
    fun write(piece: ByteArray, notify: (ByteArray) -> Unit) {
        for (f in reader.feed(piece)) if (f is Frames.Inbound.Cmd) {
            received.add(f)
            if (!mute) notify(Frames.ack(f.cmd, f.key, x = 9 + f.payload.size))   // I-18 [H]
        }
    }
}

class CoreTest {
    private val vectors: String by lazy {
        File(System.getProperty("c900.vectors") ?: "../../../tests/fixtures/c900_vectors.json").readText()
    }

    // Minimal JSON field extraction for the flat vector file (no dependency).
    private fun objects(section: String): List<Map<String, String>> {
        val body = Regex("\"$section\": \\[(.*?)\\n \\]", RegexOption.DOT_MATCHES_ALL).find(vectors)!!.groupValues[1]
        return Regex("\\{(.*?)\\}", RegexOption.DOT_MATCHES_ALL).findAll(body).map { m ->
            Regex("\"(\\w+)\": (\"[^\"]*\"|-?\\d+|null|\\[[^\\]]*\\])").findAll(m.groupValues[1])
                .associate { it.groupValues[1] to it.groupValues[2].trim('"') }
        }.toList()
    }

    @Test fun framesMatchPythonReference() {
        val fs = objects("frames")
        assertTrue(fs.size >= 5)
        for (v in fs) {
            val f = Frames.build(v["cmd"]!!.toInt(), v["key"]!!.toInt(), unhex(v["payload"]!!), v["ver"]!!.toInt())
            assertEquals(v["frame"], hex(f), v["name"])
        }
    }

    @Test fun acksMatchPythonReference() {
        for (v in objects("acks")) {
            assertEquals(v["ack"], hex(Frames.ack(v["cmd"]!!.toInt(), v["key"]!!.toInt(), v["x"]!!.toInt())), v["name"])
        }
    }

    @Test fun timeMatchesPythonAndCapture() {
        for (v in objects("times")) {
            val t = v["t"]!!.trim('[', ']').split(",").map { it.trim().toInt() }
            assertEquals(v["payload"], hex(Frames.timePayload(t[0], t[1], t[2], t[3], t[4], t[5])))
        }
        assertEquals("6a9b05cb", hex(Frames.timePayload(2026, 10, 13, 16, 23, 11)))   // C900-Q19 [H]
    }

    @Test fun hwRevisionMatchesPython() {
        for (v in objects("hw_revision")) {
            val exp = v["ver"]!!.let { if (it == "null") null else it.toInt() }
            assertEquals(exp, Frames.verFromHwRevision(v["raw"]!!.toByteArray()), v["raw"])
        }
    }

    @Test fun blockedAndAllowlist() {
        for (c in Frames.BLOCKED_CMDS) assertFailsWith<Frames.BlockedCommand> { Frames.build(c, 0) }
        assertFailsWith<IllegalArgumentException> { Commands(0x02) }
        assertTrue(Commands.ALLOWLIST.none { it.first in Frames.BLOCKED_CMDS })
        assertTrue(Commands.ALLOWLIST.none { it.first == 0x03 })   // bind is not in Phase 3a
    }

    @Test fun parseRejectsGarbage() {
        assertIs<Frames.Inbound.Bad>(Frames.parse(byteArrayOf(1, 2, 3)))
        val f = Commands(Frames.C900_VER).find(true).frame.copyOf(); f[9] = 2
        assertIs<Frames.Inbound.Bad>(Frames.parse(f))
    }

    @Test fun readerResyncsAndCaps() {
        val r = FrameReader(maxFrames = 3)
        val a = Frames.ack(2, 11, 10)
        assertEquals(1, r.feed(byteArrayOf(0, 0x11) + a.copyOf(4)).size + r.feed(a.copyOfRange(4, 9)).size)
        r.feed(a); r.feed(a)
        assertFailsWith<FrameReader.Flood> { r.feed(a) }
    }

    @Test fun denyListAndQr() {
        for (s in listOf("ff00", "0000ff10-0000-1000-8000-00805f9b34fb", "0000fff1-0000-1000-8000-00805f9b34fb", "18a8",
                "6e40ff01-b5a3-f393-e0a9-e50e24dcca9e")) assertTrue(Gatt.isDenied(s), s)
        for (s in listOf(Gatt.COMMAND_WRITE, Gatt.COMMAND_NOTIFY, "00002a19-0000-1000-8000-00805f9b34fb")) assertFalse(Gatt.isDenied(s), s)
        assertEquals("5A:1B:2C:3D:4E:6F", Gatt.macFromQr("LE:5a:1b:2c:3d:4e:6f:extra"))
        assertEquals("5A:1B:2C:3D:4E:6F", Gatt.macFromQr("https://example.invalid/d?para=5A:1B:2C:3D:4E:6F"))
        assertNull(Gatt.macFromQr("hello"))
        assertNull(Gatt.macFromQr("?para=not-a-mac"))
    }

    @Test fun messageCutsAtCharacterBoundary() {
        val m = Commands(Frames.C900_VER).message(1, "T", "é".repeat(200))
        val text = m.frame.copyOfRange(12, m.frame.size)
        assertTrue(text.size <= 196)
        assertEquals(text.size, String(text, Charsets.UTF_8).toByteArray().size)   // no broken code point
    }

    @Test fun queueOneInFlightWithSimWatch() {
        val sim = SimWatch(); val results = ArrayList<CommandQueue.Result>(); var now = 0L
        lateinit var q: CommandQueue
        val reader = FrameReader()
        q = CommandQueue(write = { p -> sim.write(p) { n -> reader.feed(n).forEach { if (it is Frames.Inbound.Ack) q.onAck(it) } } }, nowMs = { now })
        val c = Commands(Frames.C900_VER)
        q.submit(c.find(true)) { results.add(it) }
        q.submit(c.message(1, "reWatch", "test")) { results.add(it) }
        q.submit(c.time(LocalDateTime.of(2026, 10, 13, 16, 23, 11))) { results.add(it) }
        assertEquals(3, results.size)
        assertEquals(CommandQueue.Result.Ok(2, 0x0B, 10), results[0])     // x = frame length, as on hardware
        assertTrue(results.all { it is CommandQueue.Result.Ok })
        assertEquals(listOf(0x10, 0x10, 0x10), sim.received.map { it.ver })
        assertEquals(1 + 2 + 1, q.writes)                                   // message = 2 pieces
    }

    @Test fun queueTimeoutAndUnexpectedAck() {
        var now = 0L; val results = ArrayList<CommandQueue.Result>()
        val q = CommandQueue(write = {}, nowMs = { now }, timeoutMs = 1000)
        val c = Commands(Frames.C900_VER)
        q.submit(c.find(true)) { results.add(it) }
        q.submit(c.find(false)) { results.add(it) }
        now = 999; q.tick(); assertTrue(results.isEmpty())
        now = 1000; q.tick(); assertEquals("ack timeout", (results[0] as CommandQueue.Result.Failed).reason)
        q.onAck(Frames.Inbound.Ack(2, 0x01, 13, 1))
        assertTrue((results[1] as CommandQueue.Result.Failed).reason.startsWith("unexpected ack"))
        q.onAck(Frames.Inbound.Ack(2, 0x0B, 10, 1))   // unsolicited: ignored
        assertEquals(2, results.size)
    }

    @Test fun queueWriteBudget() {
        val results = ArrayList<CommandQueue.Result>()
        val q = CommandQueue(write = {}, nowMs = { 0 }, maxWritesPerSession = 1)
        q.submit(Commands(Frames.C900_VER).message(1, "reWatch", "test")) { results.add(it) }   // 25-byte frame = 2 pieces > 1
        assertEquals("session write budget reached", (results[0] as CommandQueue.Result.Failed).reason)
    }

    @Test fun sessionFlowLikeRealWatch() {
        val s = Session(); s.connecting()
        val reads = s.discovered(listOf(Gatt.COMMAND_SERVICE), listOf(Gatt.COMMAND_WRITE, Gatt.COMMAND_NOTIFY))
        assertEquals(4, reads.size)
        val feat = unhex("aacfe081dff6fc3800000000000010e64108cf1400000000000000")   // LIVE-SESSION-1 [H]
        s.readResult("00002a27-0000-1000-8000-00805f9b34fb", "10000".toByteArray())
        s.readResult("00002a26-0000-1000-8000-00805f9b34fb", "10000".toByteArray())
        s.readResult("00002a28-0000-1000-8000-00805f9b34fb", feat)
        val acts = s.readResult("00002a19-0000-1000-8000-00805f9b34fb", byteArrayOf(61))
        assertEquals(listOf<Session.Action>(Session.Action.EnableNotify), acts)
        assertEquals(Session.State.READY, s.state)
        assertEquals(0x10, s.ver); assertEquals(61, s.battery)
        assertTrue(s.bit(15, 0x40))     // pairing support set on this watch
        val bond = s.onCommand(Frames.Inbound.Cmd(0x0E, 1, 1, ByteArray(6)), 15)
        assertTrue(bond.any { it is Session.Action.AskUserBond })   // never an automatic bond
        assertIs<Session.Action.Ack>(bond[0])
    }

    @Test fun sessionRefusesUnreviewedVerAndMissingService() {
        val s = Session()
        assertIs<Session.Action.Fail>(s.discovered(listOf("0000180f-0000-1000-8000-00805f9b34fb"), emptyList()).single())
        val t = Session()
        t.discovered(listOf(Gatt.COMMAND_SERVICE), listOf(Gatt.COMMAND_WRITE, Gatt.COMMAND_NOTIFY))
        t.readResult("00002a27-0000-1000-8000-00805f9b34fb", "20000".toByteArray())
        assertIs<Session.Action.Fail>(t.readResult("00002a19-0000-1000-8000-00805f9b34fb", byteArrayOf(50)).single())
    }
}
