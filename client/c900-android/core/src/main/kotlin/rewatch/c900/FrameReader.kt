package rewatch.c900

/** Reassemble DF/FD frames from notifications with resync and hard caps (same rules as the probe). */
class FrameReader(private val maxFrames: Int = 10_000, private val maxBytes: Long = 4L * 1024 * 1024) {
    class Flood(msg: String) : IllegalStateException(msg)

    private val buf = ArrayList<Byte>()
    private var frames = 0
    private var bytes = 0L

    fun feed(data: ByteArray): List<Frames.Inbound> {
        bytes += data.size
        if (bytes > maxBytes) throw Flood("more than $maxBytes bytes")
        data.forEach { buf.add(it) }
        val out = ArrayList<Frames.Inbound>()
        while (buf.isNotEmpty()) {
            while (buf.isNotEmpty() && (buf[0].toInt() and 0xFF) !in setOf(Frames.APP_HEADER, Frames.ACK_HEADER)) buf.removeAt(0)
            if (buf.size < 3) break
            val total = (((buf[1].toInt() and 0xFF) shl 8) or (buf[2].toInt() and 0xFF)) + 4
            if (total < 9 || total > 1024) { buf.removeAt(0); continue }
            if (buf.size < total) break
            val f = ByteArray(total) { buf[it] }
            repeat(total) { buf.removeAt(0) }
            if (++frames > maxFrames) throw Flood("more than $maxFrames frames")
            out.add(Frames.parse(f))
        }
        return out
    }
}
