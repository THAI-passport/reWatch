package rewatch.c900

/**
 * History-sync tracker for inbound cmd 5 frames (PROTOCOL 7, 11). Pure logic, inbound only: it never
 * writes. Session already acks every good DF frame; this class only follows the start/end markers
 * and counts records. Built ahead of a capture of a full sync: marker keys are [C], timing is not known.
 */
class HealthSync(private val nowMs: () -> Long, private val idleTimeoutMs: Long = IDLE_TIMEOUT_MS) {
    enum class State { IDLE, SYNCING, DONE, TIMED_OUT }

    var state = State.IDLE; private set
    /** Records seen per cmd 5 key during the current sync (start and end markers excluded). */
    val counts = sortedMapOf<Int, Int>()
    var dayTotal: DayTotal? = null; private set
    private var lastAt = 0L

    /** Feed every inbound command; returns true when it was a cmd 5 frame this class consumed. */
    fun onCommand(c: Frames.Inbound.Cmd): Boolean {
        if (c.cmd != CMD) return false
        lastAt = nowMs()
        when (c.key) {
            KEY_START -> { state = State.SYNCING; counts.clear() }
            KEY_END -> if (state == State.SYNCING) state = State.DONE
            else -> {
                counts[c.key] = (counts[c.key] ?: 0) + 1
                if (c.key == KEY_DAY_TOTAL) dayTotal = DayTotal.parse(c.payload)
            }
        }
        return true
    }

    /** Call periodically; a sync with no cmd 5 frame for [idleTimeoutMs] is abandoned. */
    fun tick() {
        if (state == State.SYNCING && nowMs() - lastAt >= idleTimeoutMs) state = State.TIMED_OUT
    }

    /**
     * Key 12 day total: steps, distance, calorie as u32 BE at payload offsets 0, 4, 8 (PROTOCOL 7, C900-Q16).
     * Units [C]: the app shows distance / 1000 as km and calorie / 1000 as kcal, so the raw values are
     * meters and calories (LOG.md 2026-10-13 units trace). Null when the payload is short.
     */
    data class DayTotal(val steps: Long, val distanceM: Long, val calorieCal: Long) {
        val km get() = distanceM / 1000.0
        val kcal get() = calorieCal / 1000.0

        companion object {
            const val KEY = 12
            fun parse(p: ByteArray): DayTotal? = try {
                if (p.size < 12) null
                else {
                    val steps = u32(p, 0)
                    val dist = u32(p, 4)
                    val cal = u32(p, 8)
                    if (steps > 240000L || dist > 192000L || cal > 4464000L) {
                        DayTotal(0L, 0L, 0L)
                    } else {
                        DayTotal(steps, dist, cal)
                    }
                }
            } catch (_: Throwable) {
                null
            }

            private fun u32(p: ByteArray, o: Int): Long =
                (0 until 4).fold(0L) { acc, i -> (acc shl 8) or (p[o + i].toLong() and 0xFF) }
        }
    }

    companion object {
        const val CMD = 0x05
        const val KEY_START = 7
        const val KEY_END = 8
        const val KEY_DAY_TOTAL = 12
        /** [I] placeholder: no app timer was confirmed (R05's SPORT_DATA_TIME_OUT does not exist). */
        const val IDLE_TIMEOUT_MS = 30_000L
    }
}
