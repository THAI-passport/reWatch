package rewatch.c900

/**
 * C900 / Hiwear Plus DF/FD frame codec. Port of client/c900/frames.py (the reference); both are
 * checked against tests/fixtures/c900_vectors.json. Layout and checksum [C] PROTOCOL section 4;
 * ver byte from 0x2A27 (I-10, C900 = 0x10 [H]); watch ack x = acked frame length (I-18 [H]).
 */
object Frames {
    const val APP_HEADER = 0xDF
    const val ACK_HEADER = 0xFD
    const val DEFAULT_VER = 0x01
    const val C900_VER = 0x10
    private const val CHECKSUM_INDEX = 3
    private const val LEN_OFFSET = 4

    /** OTA, unbind, reset, factory test, factory restore, OTA new (I-20). Never built. */
    val BLOCKED_CMDS: Set<Int> = setOf(0x01, 0x04, 0x06, 0x07, 0x0D, 0x13)

    class BlockedCommand(msg: String) : IllegalArgumentException(msg)

    fun checksum(frame: ByteArray): Int {
        var s = 0
        for (i in frame.indices) if (i != CHECKSUM_INDEX) s += frame[i].toInt() and 0xFF
        return s and 0xFF
    }

    /** Internal: only [Commands] calls this, with allowlisted (cmd, key) pairs. */
    internal fun build(cmd: Int, key: Int, payload: ByteArray = ByteArray(0), ver: Int = DEFAULT_VER): ByteArray {
        require(ver in 0..0xFF) { "ver must be one byte" }
        require(cmd in 0..0xFF && key in 0..0xFF) { "cmd/key must be one byte" }
        if (cmd in BLOCKED_CMDS) throw BlockedCommand("command 0x%02X is blocked".format(cmd))
        require(payload.size <= 0xFFFF) { "payload too long" }
        val total = 9 + payload.size
        val n = total - LEN_OFFSET
        val f = ByteArray(total)
        f[0] = APP_HEADER.toByte(); f[1] = (n shr 8).toByte(); f[2] = n.toByte()
        f[4] = cmd.toByte(); f[5] = ver.toByte(); f[6] = key.toByte()
        f[7] = (payload.size shr 8).toByte(); f[8] = payload.size.toByte()
        payload.copyInto(f, 9)
        f[CHECKSUM_INDEX] = checksum(f).toByte()
        return f
    }

    fun ack(cmd: Int, key: Int, x: Int, status: Int = 1): ByteArray {
        require(x in 0..0xFFFF)
        val f = byteArrayOf(ACK_HEADER.toByte(), 0, 5, 0, cmd.toByte(), key.toByte(), (x shr 8).toByte(), x.toByte(), status.toByte())
        f[CHECKSUM_INDEX] = checksum(f).toByte()
        return f
    }

    sealed class Inbound {
        data class Cmd(val cmd: Int, val ver: Int, val key: Int, val payload: ByteArray) : Inbound() {
            // Structural equality on the payload (R07): the data-class default compares array identity.
            override fun equals(other: Any?): Boolean = other is Cmd && cmd == other.cmd && ver == other.ver &&
                key == other.key && payload.contentEquals(other.payload)
            override fun hashCode(): Int = ((cmd * 31 + ver) * 31 + key) * 31 + payload.contentHashCode()
        }
        data class Ack(val cmd: Int, val key: Int, val x: Int, val status: Int) : Inbound()
        data class Bad(val reason: String) : Inbound()
    }

    /** Parse one complete frame. Never throws on garbage. */
    fun parse(frame: ByteArray): Inbound {
        if (frame.size < 9) return Inbound.Bad("short")
        val h = frame[0].toInt() and 0xFF
        if (h != APP_HEADER && h != ACK_HEADER) return Inbound.Bad("header")
        val len = ((frame[1].toInt() and 0xFF) shl 8) or (frame[2].toInt() and 0xFF)
        if (len + LEN_OFFSET != frame.size) return Inbound.Bad("length")
        if (checksum(frame) != (frame[CHECKSUM_INDEX].toInt() and 0xFF)) return Inbound.Bad("checksum")
        val u = { i: Int -> frame[i].toInt() and 0xFF }
        if (h == ACK_HEADER) return Inbound.Ack(u(4), u(5), (u(6) shl 8) or u(7), u(8))
        val plen = (u(7) shl 8) or u(8)
        if (9 + plen > frame.size) return Inbound.Bad("plen")
        return Inbound.Cmd(u(4), u(5), u(6), frame.copyOfRange(9, 9 + plen))
    }

    /** ver byte the app derives from 0x2A27: strip V/v, digits before the first dot, low 8 bits. */
    fun verFromHwRevision(raw: ByteArray?): Int? {
        var s = (raw ?: return null).toString(Charsets.US_ASCII).trim()
        if (s.startsWith("V") || s.startsWith("v")) s = s.substring(1)
        val digits = s.substringBefore('.')
        if (digits.isEmpty() || digits.length > 9 || !digits.all { it in '0'..'9' }) return null
        return (digits.toLong() and 0xFF).toInt()
    }

    /** 4 packed bytes, year-2000 (I-21 [C]+[H]). */
    fun timePayload(year: Int, month: Int, day: Int, hour: Int, minute: Int, second: Int): ByteArray {
        require(year in 2000..2063 && month in 1..12 && day in 1..31 && hour in 0..23 && minute in 0..59 && second in 0..59) { "time out of range" }
        val y = year - 2000
        return byteArrayOf(
            ((y shl 2) + (month shr 2)).toByte(),
            (((month and 3) shl 6) + (day shl 1) + (hour shr 4)).toByte(),
            (((hour and 15) shl 4) + (minute shr 2)).toByte(),
            (((minute and 3) shl 6) + second).toByte(),
        )
    }
}
