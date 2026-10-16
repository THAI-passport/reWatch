package rewatch.c900

import java.time.LocalDateTime

/**
 * The only way to build a frame in the client: one function per allowlisted (cmd, key) pair.
 * Phase 3a/3b set (CLIENT-DESIGN section 8). Bind, OTA, faces and contacts are not here.
 */
class Commands(val ver: Int) {
    init { require(ver in REVIEWED_VERS) { "ver 0x%02x not reviewed".format(ver) } }

    data class Out(val cmd: Int, val key: Int, val frame: ByteArray)

    fun time(now: LocalDateTime): Out =
        out(0x02, 0x01, Frames.timePayload(now.year, now.monthValue, now.dayOfMonth, now.hour, now.minute, now.second))

    fun find(on: Boolean): Out = out(0x02, 0x0B, byteArrayOf(if (on) 1 else 0))

    /** Message push, cmd 2 key 18: type, 0, 0, UTF-8 "title:body" cut at 196 bytes [C]. */
    fun message(type: Int, title: String, body: String): Out {
        require(type in 1..0xFF)
        val text = cutUtf8("$title:$body", 196)
        return out(0x02, 0x12, byteArrayOf(type.toByte(), 0, 0) + text)
    }

    /** 12/24 h: payload 1 = 12 h, 0 = 24 h (I-22). */
    fun hourFormat(twelveHour: Boolean): Out = out(0x02, 0x1A, byteArrayOf(if (twelveHour) 1 else 0))

    /** Feature map query, cmd 0x19 key 0 (read-like). */
    fun featuresQuery(): Out = out(0x19, 0x00, ByteArray(0))

    private fun out(cmd: Int, key: Int, payload: ByteArray): Out {
        check((cmd to key) in ALLOWLIST) { "internal: not allowlisted" }
        return Out(cmd, key, Frames.build(cmd, key, payload, ver))
    }

    companion object {
        val REVIEWED_VERS = setOf(Frames.DEFAULT_VER, Frames.C900_VER)
        val ALLOWLIST = setOf(0x02 to 0x01, 0x02 to 0x0B, 0x02 to 0x12, 0x02 to 0x1A, 0x19 to 0x00)

        /** Cut UTF-8 at a character boundary so the watch never gets half a code point. */
        fun cutUtf8(s: String, max: Int): ByteArray {
            val b = s.toByteArray(Charsets.UTF_8)
            if (b.size <= max) return b
            var n = max
            while (n > 0 && (b[n].toInt() and 0xC0) == 0x80) n--
            return b.copyOf(n)
        }
    }
}
