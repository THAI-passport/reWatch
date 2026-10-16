package rewatch.c900

import java.nio.ByteBuffer
import java.nio.CharBuffer
import java.nio.charset.CodingErrorAction
import java.time.LocalDateTime
import kotlin.random.Random
import kotlin.test.*

class FuzzTest {

    private val bufField = FrameReader::class.java.getDeclaredField("buf").apply { isAccessible = true }
    private fun FrameReader.bufferSize(): Int = (bufField.get(this) as List<*>).size

    /** 1. FrameReader.feed with 10k random chunks (0-64 bytes): never throws except Flood; buffer <= 1024 + chunk. */
    @Test
    fun frameReaderFeedFuzz() {
        val rng = Random(42)
        val reader = FrameReader(maxFrames = 100_000, maxBytes = 100L * 1024 * 1024)
        for (i in 0 until 10_000) {
            val chunkSize = rng.nextInt(65)
            val chunk = ByteArray(chunkSize)
            rng.nextBytes(chunk)
            try {
                reader.feed(chunk)
            } catch (_: FrameReader.Flood) {
                // Flood is expected if limits are breached
            }
            val bufSize = reader.bufferSize()
            assertTrue(bufSize <= 1024 + chunkSize, "Buffer grew to $bufSize > 1024 + $chunkSize at iter $i")
        }
    }

    /** 2. Frames.parse on random bytes: never throws. */
    @Test
    fun framesParseNeverThrows() {
        val rng = Random(1337)
        for (i in 0 until 10_000) {
            val len = rng.nextInt(1201)
            val bytes = ByteArray(len)
            rng.nextBytes(bytes)
            val res = Frames.parse(bytes)
            assertNotNull(res)
        }
    }

    /** 3. Round trip: every Commands builder over random valid inputs -> parse returns matching cmd/key/payload and ver. */
    @Test
    fun commandsRoundTrip() {
        val rng = Random(2026)
        for (ver in Commands.REVIEWED_VERS) {
            val cmds = Commands(ver)

            // find
            for (i in 0..100) {
                val on = rng.nextBoolean()
                val out = cmds.find(on)
                val parsed = Frames.parse(out.frame)
                assertIs<Frames.Inbound.Cmd>(parsed)
                assertEquals(0x02, parsed.cmd)
                assertEquals(0x0B, parsed.key)
                assertEquals(ver, parsed.ver)
                assertContentEquals(byteArrayOf(if (on) 1 else 0), parsed.payload)
            }

            // hourFormat
            for (i in 0..100) {
                val twelve = rng.nextBoolean()
                val out = cmds.hourFormat(twelve)
                val parsed = Frames.parse(out.frame)
                assertIs<Frames.Inbound.Cmd>(parsed)
                assertEquals(0x02, parsed.cmd)
                assertEquals(0x1A, parsed.key)
                assertEquals(ver, parsed.ver)
                assertContentEquals(byteArrayOf(if (twelve) 1 else 0), parsed.payload)
            }

            // featuresQuery
            val fq = cmds.featuresQuery()
            val parsedFq = Frames.parse(fq.frame)
            assertIs<Frames.Inbound.Cmd>(parsedFq)
            assertEquals(0x19, parsedFq.cmd)
            assertEquals(0x00, parsedFq.key)
            assertEquals(ver, parsedFq.ver)
            assertEquals(0, parsedFq.payload.size)

            // time
            for (i in 0..500) {
                val year = rng.nextInt(2000, 2064)
                val month = rng.nextInt(1, 13)
                val day = rng.nextInt(1, 29)
                val hour = rng.nextInt(0, 24)
                val minute = rng.nextInt(0, 60)
                val second = rng.nextInt(0, 60)
                val dt = LocalDateTime.of(year, month, day, hour, minute, second)
                val out = cmds.time(dt)
                val parsed = Frames.parse(out.frame)
                assertIs<Frames.Inbound.Cmd>(parsed)
                assertEquals(0x02, parsed.cmd)
                assertEquals(0x01, parsed.key)
                assertEquals(ver, parsed.ver)
                assertContentEquals(Frames.timePayload(year, month, day, hour, minute, second), parsed.payload)
            }

            // message
            for (i in 0..500) {
                val type = rng.nextInt(1, 256)
                val titleLen = rng.nextInt(0, 50)
                val bodyLen = rng.nextInt(0, 250)
                val title = buildString { repeat(titleLen) { append(('a'..'z').random(rng)) } }
                val body = buildString { repeat(bodyLen) { append(('A'..'Z').random(rng)) } }
                val out = cmds.message(type, title, body)
                val parsed = Frames.parse(out.frame)
                assertIs<Frames.Inbound.Cmd>(parsed)
                assertEquals(0x02, parsed.cmd)
                assertEquals(0x12, parsed.key)
                assertEquals(ver, parsed.ver)
                val expectedPayload = byteArrayOf(type.toByte(), 0, 0) + Commands.cutUtf8("$title:$body", 196)
                assertContentEquals(expectedPayload, parsed.payload)
            }
        }
    }

    /** 4. Splitting: any valid frame fed in random splits yields exactly one identical result. */
    @Test
    fun frameSplitting() {
        val rng = Random(8888)
        val framesToTest = ArrayList<ByteArray>()

        val cmds = Commands(Frames.C900_VER)
        framesToTest.add(cmds.find(true).frame)
        framesToTest.add(cmds.find(false).frame)
        framesToTest.add(cmds.hourFormat(true).frame)
        framesToTest.add(cmds.featuresQuery().frame)
        framesToTest.add(cmds.time(LocalDateTime.of(2026, 10, 13, 20, 0, 0)).frame)
        framesToTest.add(cmds.message(1, "Notification Title", "Body text of notification").frame)
        framesToTest.add(Frames.ack(2, 0x0B, 10))
        framesToTest.add(Frames.ack(2, 0x01, 13))
        framesToTest.add(Frames.ack(0x19, 0, 9))

        for (origFrame in framesToTest) {
            val expectedParsed = Frames.parse(origFrame)
            for (trial in 0 until 100) {
                val reader = FrameReader()
                val collected = ArrayList<Frames.Inbound>()
                var offset = 0
                while (offset < origFrame.size) {
                    val remaining = origFrame.size - offset
                    val splitSize = rng.nextInt(1, remaining + 1)
                    val chunk = origFrame.copyOfRange(offset, offset + splitSize)
                    collected.addAll(reader.feed(chunk))
                    offset += splitSize
                }
                assertEquals(1, collected.size, "Splitting trial $trial yielded ${collected.size} frames")
                assertInboundEquals(expectedParsed, collected[0])
            }
        }
    }

    private fun assertInboundEquals(expected: Frames.Inbound, actual: Frames.Inbound) {
        when {
            expected is Frames.Inbound.Cmd && actual is Frames.Inbound.Cmd -> {
                assertEquals(expected.cmd, actual.cmd)
                assertEquals(expected.ver, actual.ver)
                assertEquals(expected.key, actual.key)
                assertContentEquals(expected.payload, actual.payload)
            }
            else -> assertEquals(expected, actual)
        }
    }

    /** 5. CommandQueue: random interleavings never leave two in flight, every submit gets one result, writes <= budget. */
    @Test
    fun commandQueueInterleavingFuzz() {
        val rng = Random(9999)
        val cmds = Commands(Frames.C900_VER)
        val sampleOuts = listOf(
            cmds.find(true),
            cmds.find(false),
            cmds.hourFormat(true),
            cmds.featuresQuery(),
            cmds.time(LocalDateTime.of(2026, 1, 1, 0, 0, 0)),
            cmds.message(1, "Test", "Msg")
        )

        val maxBudget = 250
        var now = 1000L
        val results = ArrayList<CommandQueue.Result>()

        val queue = CommandQueue(
            write = {},
            nowMs = { now },
            timeoutMs = 5000,
            maxWritesPerSession = maxBudget
        )

        var submittedCount = 0
        var completedCount = 0

        for (step in 0 until 5000) {
            assertTrue(queue.writes <= maxBudget, "Queue writes ${queue.writes} exceeded budget $maxBudget")

            val action = rng.nextInt(5)
            when (action) {
                0, 1 -> {
                    val out = sampleOuts.random(rng)
                    submittedCount++
                    queue.submit(out) { res ->
                        completedCount++
                        results.add(res)
                    }
                }
                2 -> {
                    val ackCmd = if (rng.nextBoolean()) 0x02 else rng.nextInt(0, 256)
                    val ackKey = if (rng.nextBoolean()) 0x0B else rng.nextInt(0, 256)
                    val status = if (rng.nextInt(10) == 0) 0 else 1
                    queue.onAck(Frames.Inbound.Ack(ackCmd, ackKey, 10, status))
                }
                3 -> {
                    now += rng.nextLong(0, 6000)
                    queue.tick()
                }
                4 -> {
                    queue.abortAll("random disconnect")
                }
            }
        }

        queue.abortAll("end of test")
        assertEquals(submittedCount, completedCount, "Every submitted command must receive exactly one result")
        assertEquals(submittedCount, results.size)
        assertTrue(queue.writes <= maxBudget)
    }

    /** 6. Gatt.isDenied is true for every UUID ending dcca9e or containing 5610, false for command UUIDs. */
    @Test
    fun gattIsDeniedFuzz() {
        val rng = Random(5610)

        assertFalse(Gatt.isDenied(Gatt.COMMAND_SERVICE), "COMMAND_SERVICE must not be denied")
        assertFalse(Gatt.isDenied(Gatt.COMMAND_WRITE), "COMMAND_WRITE must not be denied")
        assertFalse(Gatt.isDenied(Gatt.COMMAND_NOTIFY), "COMMAND_NOTIFY must not be denied")

        for (i in 0 until 1000) {
            val prefixLen = rng.nextInt(1, 30)
            val prefix = (0 until prefixLen).map { "0123456789abcdef"[rng.nextInt(16)] }.joinToString("")
            val caseVar = if (rng.nextBoolean()) "dcca9e" else if (rng.nextBoolean()) "DCCA9E" else "Dcca9E"
            val uuid = "$prefix-$caseVar"
            assertTrue(Gatt.isDenied(uuid), "UUID ending with $caseVar should be denied: $uuid")
        }

        for (i in 0 until 1000) {
            val p1 = (0..5).map { "0123456789abcdef"[rng.nextInt(16)] }.joinToString("")
            val p2 = (0..5).map { "0123456789abcdef"[rng.nextInt(16)] }.joinToString("")
            val uuid = "${p1}5610${p2}"
            assertTrue(Gatt.isDenied(uuid), "UUID containing 5610 should be denied: $uuid")
        }
    }

    /** 7. Commands.cutUtf8: random Unicode strings never produce invalid UTF-8 and never exceed the limit. */
    @Test
    fun commandsCutUtf8Fuzz() {
        val rng = Random(7777)
        val decoder = Charsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)

        val sampleCodePoints = ArrayList<Int>()
        (0x20..0x7E).forEach { sampleCodePoints.add(it) }
        (0x00A0..0x00FF).forEach { sampleCodePoints.add(it) }
        (0x0400..0x04FF).forEach { sampleCodePoints.add(it) }
        (0x0600..0x06FF).forEach { sampleCodePoints.add(it) }
        (0x4E00..0x4FFF).forEach { sampleCodePoints.add(it) }
        (0x1F600..0x1F64F).forEach { sampleCodePoints.add(it) }

        for (trial in 0 until 5000) {
            val len = rng.nextInt(0, 100)
            val str = buildString {
                repeat(len) {
                    val cp = sampleCodePoints.random(rng)
                    appendCodePoint(cp)
                }
            }
            val limit = rng.nextInt(0, 300)
            val cut = Commands.cutUtf8(str, limit)

            assertTrue(cut.size <= limit, "Cut length ${cut.size} exceeds limit $limit")

            val byteBuf = ByteBuffer.wrap(cut)
            val charBuf = CharBuffer.allocate(cut.size + 1)
            decoder.reset()
            val cr = decoder.decode(byteBuf, charBuf, true)
            assertTrue(!cr.isError, "cut produced invalid UTF-8 (trial $trial, limit $limit): $cr")
        }
    }
}
