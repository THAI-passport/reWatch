package rewatch.c900.app

/**
 * Pure deduplication logic for health records (no Android dependencies).
 * Enforces composite key uniqueness per record kind so repeated syncs do not duplicate rows.
 */
object HealthDeduplicator {

    data class HourlyStepEntity(
        val date: String,
        val hour: Int,
        val steps: Int,
        val distanceM: Int,
        val calorieCal: Long
    )

    data class HeartRateEntity(
        val date: String,
        val secondsOfDay: Long,
        val rawType: Int,
        val bpm: Int
    )

    data class BloodPressureEntity(
        val date: String,
        val secondsOfDay: Long,
        val systolic: Int,
        val diastolic: Int
    )

    data class SleepSummaryEntity(
        val date: String,
        val startMinutes: Int,
        val lightMinutes: Int,
        val deepMinutes: Int,
        val endMinutes: Int,
        val awakeMinutes: Int
    ) {
        val totalSleepMinutes get() = lightMinutes + deepMinutes
    }

    data class DayTotalEntity(
        val date: String,
        val steps: Long,
        val distanceM: Long,
        val calorieCal: Long
    ) {
        val km get() = distanceM / 1000.0
        val kcal get() = calorieCal / 1000.0
    }

    data class TemperatureEntity(
        val date: String,
        val secondsOfDay: Long,
        val rawType: Int,
        val degrees: Int,
        val tenths: Int,
        val tempC: Double
    )

    data class SpO2Entity(
        val date: String,
        val secondsOfDay: Long,
        val percent: Int
    )

    data class SportSessionEntity(
        val date: String,
        val startSeconds: Long,
        val endSeconds: Long,
        val durationSeconds: Long,
        val mode: Int,
        val heartRate: Int,
        val calorieCal: Long,
        val raw1: Long,
        val raw2: Long,
        val raw3: Long
    )

    /** Generic deduplicator merging existing and incoming records by key, with incoming replacing existing. */
    fun <T, K> dedupe(existing: List<T>, incoming: List<T>, keySelector: (T) -> K): List<T> {
        val map = LinkedHashMap<K, T>()
        for (item in existing) {
            map[keySelector(item)] = item
        }
        for (item in incoming) {
            map[keySelector(item)] = item
        }
        return map.values.toList()
    }

    fun dedupeHourlySteps(existing: List<HourlyStepEntity>, incoming: List<HourlyStepEntity>): List<HourlyStepEntity> =
        dedupe(existing, incoming) { Pair(it.date, it.hour) }

    fun dedupeHeartRate(existing: List<HeartRateEntity>, incoming: List<HeartRateEntity>): List<HeartRateEntity> =
        dedupe(existing, incoming) { Pair(it.date, it.secondsOfDay) }

    fun dedupeBloodPressure(existing: List<BloodPressureEntity>, incoming: List<BloodPressureEntity>): List<BloodPressureEntity> =
        dedupe(existing, incoming) { Pair(it.date, it.secondsOfDay) }

    fun dedupeSleep(existing: List<SleepSummaryEntity>, incoming: List<SleepSummaryEntity>): List<SleepSummaryEntity> =
        dedupe(existing, incoming) { it.date }

    fun dedupeDayTotal(existing: List<DayTotalEntity>, incoming: List<DayTotalEntity>): List<DayTotalEntity> =
        dedupe(existing, incoming) { it.date }

    fun dedupeTemperature(existing: List<TemperatureEntity>, incoming: List<TemperatureEntity>): List<TemperatureEntity> =
        dedupe(existing, incoming) { Pair(it.date, it.secondsOfDay) }

    fun dedupeSpO2(existing: List<SpO2Entity>, incoming: List<SpO2Entity>): List<SpO2Entity> =
        dedupe(existing, incoming) { Pair(it.date, it.secondsOfDay) }

    fun dedupeSportSessions(existing: List<SportSessionEntity>, incoming: List<SportSessionEntity>): List<SportSessionEntity> =
        dedupe(existing, incoming) { Pair(it.date, it.startSeconds) }
}
