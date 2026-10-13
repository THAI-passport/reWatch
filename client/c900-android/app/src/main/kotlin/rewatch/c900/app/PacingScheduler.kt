package rewatch.c900.app

import rewatch.c900.Gatt

sealed class GattOp {
    data class Read(val uuid: String) : GattOp()
    data class WritePiece(val piece: ByteArray) : GattOp() {
        override fun equals(other: Any?): Boolean = other is WritePiece && piece.contentEquals(other.piece)
        override fun hashCode(): Int = piece.contentHashCode()
    }
    object EnableNotify : GattOp()
}

/**
 * Pacing scheduler for GATT operations.
 * Enforces strictly ONE in-flight GATT operation at a time, and spaces ATT piece writes
 * at least [Gatt.PIECE_GAP_MS] apart.
 * Rejects any operation targeting denied UUIDs (I-14, I-54).
 */
class PacingScheduler(
    private val execute: (GattOp) -> Unit,
    private val postDelayed: (delayMs: Long, task: () -> Unit) -> Unit,
    private val nowMs: () -> Long = { System.currentTimeMillis() },
    private val pieceGapMs: Long = Gatt.PIECE_GAP_MS
) {
    private val queue = ArrayDeque<GattOp>()
    private var inFlight: GattOp? = null
    private var lastWriteAt = 0L

    val isBusy: Boolean
        @Synchronized get() = inFlight != null

    val queuedCount: Int
        @Synchronized get() = queue.size

    @Synchronized
    fun enqueue(op: GattOp) {
        // Drop any operation targeting denied UUIDs (I-14, I-54)
        if (op is GattOp.Read && Gatt.isDenied(op.uuid)) return
        queue.addLast(op)
        pump()
    }

    @Synchronized
    fun onComplete(op: GattOp) {
        if (inFlight == op) {
            inFlight = null
            pump()
        }
    }

    @Synchronized
    fun clear() {
        queue.clear()
        inFlight = null
        lastWriteAt = 0L
    }

    @Synchronized
    private fun pump() {
        if (inFlight != null) return
        val next = queue.firstOrNull() ?: return

        if (next is GattOp.WritePiece) {
            val elapsedSinceLast = nowMs() - lastWriteAt
            if (elapsedSinceLast < pieceGapMs && lastWriteAt > 0L) {
                val delay = pieceGapMs - elapsedSinceLast
                postDelayed(delay) {
                    synchronized(this) {
                        pump()
                    }
                }
                return
            }
        }

        queue.removeFirst()
        inFlight = next
        if (next is GattOp.WritePiece) {
            lastWriteAt = nowMs()
        }
        execute(next)
    }
}
