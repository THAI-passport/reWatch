package rewatch.c900

/**
 * One command in flight (I-15). The caller provides the clock and the writer; this class only
 * decides. Ack matches by cmd and key; status 1 = ok. No automatic resend (CLIENT-DESIGN 3.3).
 */
class CommandQueue(
    private val write: (ByteArray) -> Unit,
    private val nowMs: () -> Long,
    private val timeoutMs: Long = 100_000,       // app value, I-15 [C smali]
    private val maxWritesPerSession: Int = 200,  // write budget until flash cost is known (ground rule 7)
) {
    sealed class Result {
        data class Ok(val cmd: Int, val key: Int, val x: Int) : Result()
        data class Failed(val cmd: Int, val key: Int, val reason: String) : Result()
    }

    private data class Pending(val out: Commands.Out, val onDone: (Result) -> Unit)

    private val queue = ArrayDeque<Pending>()
    private var inFlight: Pending? = null
    private var sentAt = 0L
    var writes = 0
        private set

    fun submit(out: Commands.Out, onDone: (Result) -> Unit) {
        queue.addLast(Pending(out, onDone))
        pump()
    }

    val busy get() = inFlight != null

    fun onAck(a: Frames.Inbound.Ack) {
        val p = inFlight ?: return            // unsolicited ack: ignored, never matched later
        inFlight = null
        val r = when {
            a.cmd != p.out.cmd || a.key != p.out.key -> Result.Failed(p.out.cmd, p.out.key, "unexpected ack 0x%02x/%d".format(a.cmd, a.key))
            a.status != 1 -> Result.Failed(p.out.cmd, p.out.key, "status ${a.status}")
            else -> Result.Ok(a.cmd, a.key, a.x)
        }
        p.onDone(r)
        pump()
    }

    /** Call periodically; fails the in-flight command after the timeout. */
    fun tick() {
        val p = inFlight ?: return
        if (nowMs() - sentAt >= timeoutMs) {
            inFlight = null
            p.onDone(Result.Failed(p.out.cmd, p.out.key, "ack timeout"))
            pump()
        }
    }

    /** Disconnect: everything pending fails, nothing is resent later. */
    fun abortAll(reason: String) {
        (listOfNotNull(inFlight) + queue).forEach { it.onDone(Result.Failed(it.out.cmd, it.out.key, reason)) }
        inFlight = null
        queue.clear()
    }

    private fun pump() {
        if (inFlight != null) return
        val p = queue.removeFirstOrNull() ?: return
        val pieces = Gatt.pieces(p.out.frame)
        if (writes + pieces.size > maxWritesPerSession) {
            p.onDone(Result.Failed(p.out.cmd, p.out.key, "session write budget reached"))
            pump(); return
        }
        inFlight = p
        sentAt = nowMs()
        pieces.forEach { writes++; write(it) }
    }
}
