package rewatch.c900

/**
 * Parsed health records collected during a history sync (cmd 5).
 * Exposed when HealthSync reaches State.DONE.
 */
data class SyncedHealthData(
    val hourlySteps: List<HourlySteps> = emptyList(),
    val heartRates: List<HeartRate> = emptyList(),
    val bloodPressures: List<BloodPressure> = emptyList(),
    val sleepSummaries: List<SleepSummary> = emptyList(),
    val dayTotal: HealthSync.DayTotal? = null,
    val temperatures: List<Temperature> = emptyList(),
    val spo2Records: List<SpO2Record> = emptyList(),
    val sportSessions: List<SportSessions> = emptyList()
)

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

    private val _hourlySteps = mutableListOf<HourlySteps>()
    private val _heartRates = mutableListOf<HeartRate>()
    private val _bloodPressures = mutableListOf<BloodPressure>()
    private val _sleepSummaries = mutableListOf<SleepSummary>()
    private val _temperatures = mutableListOf<Temperature>()
    private val _spo2Records = mutableListOf<SpO2Record>()
    private val _sportSessions = mutableListOf<SportSessions>()

    /** Exposes all parsed health records when the sync finishes successfully (State.DONE). Null otherwise. */
    var syncedData: SyncedHealthData? = null; private set

    val hourlySteps: List<HourlySteps> get() = syncedData?.hourlySteps ?: emptyList()
    val heartRates: List<HeartRate> get() = syncedData?.heartRates ?: emptyList()
    val bloodPressures: List<BloodPressure> get() = syncedData?.bloodPressures ?: emptyList()
    val sleepSummaries: List<SleepSummary> get() = syncedData?.sleepSummaries ?: emptyList()
    val temperatures: List<Temperature> get() = syncedData?.temperatures ?: emptyList()
    val spo2Records: List<SpO2Record> get() = syncedData?.spo2Records ?: emptyList()
    val sportSessions: List<SportSessions> get() = syncedData?.sportSessions ?: emptyList()

    /** Feed every inbound command; returns true when it was a cmd 5 frame this class consumed. */
    fun onCommand(c: Frames.Inbound.Cmd): Boolean {
        if (c.cmd != CMD) return false
        lastAt = nowMs()
        when (c.key) {
            KEY_START -> {
                state = State.SYNCING
                counts.clear()
                _hourlySteps.clear()
                _heartRates.clear()
                _bloodPressures.clear()
                _sleepSummaries.clear()
                dayTotal = null
                _temperatures.clear()
                _spo2Records.clear()
                _sportSessions.clear()
                syncedData = null
            }
            KEY_END -> {
                if (state == State.SYNCING) {
                    state = State.DONE
                    syncedData = SyncedHealthData(
                        hourlySteps = _hourlySteps.toList(),
                        heartRates = _heartRates.toList(),
                        bloodPressures = _bloodPressures.toList(),
                        sleepSummaries = _sleepSummaries.toList(),
                        dayTotal = dayTotal,
                        temperatures = _temperatures.toList(),
                        spo2Records = _spo2Records.toList(),
                        sportSessions = _sportSessions.toList()
                    )
                }
            }
            else -> {
                counts[c.key] = (counts[c.key] ?: 0) + 1
                when (c.key) {
                    HourlySteps.KEY -> HourlySteps.parse(c.payload)?.let { _hourlySteps.add(it) }
                    HeartRate.KEY -> HeartRate.parse(c.payload)?.let { _heartRates.add(it) }
                    BloodPressure.KEY -> BloodPressure.parse(c.payload)?.let { _bloodPressures.add(it) }
                    SleepSummary.KEY -> SleepSummary.parse(c.payload)?.let { _sleepSummaries.add(it) }
                    KEY_DAY_TOTAL -> DayTotal.parse(c.payload)?.let { dayTotal = it }
                    Temperature.KEY -> Temperature.parse(c.payload)?.let { _temperatures.add(it) }
                    SpO2Record.KEY -> SpO2Record.parse(c.payload)?.let { _spo2Records.add(it) }
                    SportSessions.KEY -> SportSessions.parse(c.payload)?.let { _sportSessions.add(it) }
                }
            }
        }
        return true
    }

    /** Call periodically; a sync with no cmd 5 frame for [idleTimeoutMs] is abandoned. */
    fun tick() {
        if (state == State.SYNCING && nowMs() - lastAt >= idleTimeoutMs) {
            state = State.TIMED_OUT
            syncedData = null
        }
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
