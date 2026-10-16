package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Test
import rewatch.c900.app.HealthDeduplicator.BloodPressureEntity
import rewatch.c900.app.HealthDeduplicator.DayTotalEntity
import rewatch.c900.app.HealthDeduplicator.HeartRateEntity
import rewatch.c900.app.HealthDeduplicator.HourlyStepEntity
import rewatch.c900.app.HealthDeduplicator.SleepSummaryEntity
import rewatch.c900.app.HealthDeduplicator.SpO2Entity
import rewatch.c900.app.HealthDeduplicator.SportSessionEntity
import rewatch.c900.app.HealthDeduplicator.TemperatureEntity

/**
 * Unit tests verifying health record deduplication as a pure function (Task A3).
 * Proves that repeated syncs do not duplicate records for identical (date, time) composite keys.
 */
class HealthDedupeTest {

    @Test
    fun dedupeHourlyStepsByDateAndHour() {
        // Initial sync: hours 6, 7, 8 on 2026-10-13
        val existing = listOf(
            HourlyStepEntity("2026-10-13", 6, steps = 100, distanceM = 70, calorieCal = 3000),
            HourlyStepEntity("2026-10-13", 7, steps = 500, distanceM = 350, calorieCal = 15000),
            HourlyStepEntity("2026-10-13", 8, steps = 200, distanceM = 140, calorieCal = 6000)
        )

        // Repeated sync: hour 8 updated with new steps, hour 9 added
        val incoming = listOf(
            HourlyStepEntity("2026-10-13", 8, steps = 800, distanceM = 560, calorieCal = 24000),
            HourlyStepEntity("2026-10-13", 9, steps = 1200, distanceM = 840, calorieCal = 36000)
        )

        val result = HealthDeduplicator.dedupeHourlySteps(existing, incoming)

        // Should have exactly 4 hours (6, 7, 8, 9) with no duplicated hour 8
        assertEquals(4, result.size)
        val byHour = result.associateBy { it.hour }
        assertEquals(100, byHour[6]!!.steps)
        assertEquals(500, byHour[7]!!.steps)
        assertEquals(800, byHour[8]!!.steps) // updated by incoming
        assertEquals(1200, byHour[9]!!.steps)

        // Idempotency: re-running with identical data does not alter count
        val reRun = HealthDeduplicator.dedupeHourlySteps(result, incoming)
        assertEquals(4, reRun.size)
    }

    @Test
    fun dedupeHeartRateByDateAndSecondsOfDay() {
        val existing = listOf(
            HeartRateEntity("2026-10-13", 27000L, rawType = 1, bpm = 70),
            HeartRateEntity("2026-10-13", 28800L, rawType = 1, bpm = 75)
        )
        val incoming = listOf(
            HeartRateEntity("2026-10-13", 27000L, rawType = 1, bpm = 72), // duplicate timestamp, new bpm
            HeartRateEntity("2026-10-13", 30000L, rawType = 1, bpm = 80)
        )

        val result = HealthDeduplicator.dedupeHeartRate(existing, incoming)
        assertEquals(3, result.size)
        val bySeconds = result.associateBy { it.secondsOfDay }
        assertEquals(72, bySeconds[27000L]!!.bpm) // replaced
        assertEquals(75, bySeconds[28800L]!!.bpm)
        assertEquals(80, bySeconds[30000L]!!.bpm)
    }

    @Test
    fun dedupeBloodPressureByDateAndSecondsOfDay() {
        val existing = listOf(
            BloodPressureEntity("2026-10-13", 27000L, systolic = 115, diastolic = 75)
        )
        val incoming = listOf(
            BloodPressureEntity("2026-10-13", 27000L, systolic = 118, diastolic = 76),
            BloodPressureEntity("2026-10-13", 36000L, systolic = 120, diastolic = 80)
        )

        val result = HealthDeduplicator.dedupeBloodPressure(existing, incoming)
        assertEquals(2, result.size)
        assertEquals(118, result[0].systolic)
        assertEquals(76, result[0].diastolic)
        assertEquals(120, result[1].systolic)
    }

    @Test
    fun dedupeSleepByDate() {
        val existing = listOf(
            SleepSummaryEntity("2026-10-12", 1380, 200, 100, 400, 10),
            SleepSummaryEntity("2026-10-13", 1380, 180, 90, 390, 15)
        )
        val incoming = listOf(
            SleepSummaryEntity("2026-10-13", 1380, 240, 120, 420, 15), // re-sync updated sleep for today
            SleepSummaryEntity("2026-10-14", 1380, 210, 110, 410, 10)
        )

        val result = HealthDeduplicator.dedupeSleep(existing, incoming)
        assertEquals(3, result.size)
        val byDate = result.associateBy { it.date }
        assertEquals(240, byDate["2026-10-13"]!!.lightMinutes)
        assertEquals(360, byDate["2026-10-13"]!!.totalSleepMinutes)
    }

    @Test
    fun dedupeDayTotalByDate() {
        val existing = listOf(
            DayTotalEntity("2026-10-13", steps = 5000, distanceM = 3500, calorieCal = 150000)
        )
        val incoming = listOf(
            DayTotalEntity("2026-10-13", steps = 8000, distanceM = 5600, calorieCal = 240000)
        )

        val result = HealthDeduplicator.dedupeDayTotal(existing, incoming)
        assertEquals(1, result.size)
        assertEquals(8000L, result[0].steps)
        assertEquals(5.6, result[0].km, 1e-6)
    }

    @Test
    fun dedupeTemperatureByDateAndSecondsOfDay() {
        val existing = listOf(
            TemperatureEntity("2026-10-13", 27000L, 1, 36, 4, 36.4)
        )
        val incoming = listOf(
            TemperatureEntity("2026-10-13", 27000L, 1, 36, 6, 36.6),
            TemperatureEntity("2026-10-13", 28000L, 1, 36, 7, 36.7)
        )

        val result = HealthDeduplicator.dedupeTemperature(existing, incoming)
        assertEquals(2, result.size)
        assertEquals(36.6, result[0].tempC, 1e-6)
    }

    @Test
    fun dedupeSpO2ByDateAndSecondsOfDay() {
        val existing = listOf(
            SpO2Entity("2026-10-13", 27000L, percent = 97)
        )
        val incoming = listOf(
            SpO2Entity("2026-10-13", 27000L, percent = 98)
        )

        val result = HealthDeduplicator.dedupeSpO2(existing, incoming)
        assertEquals(1, result.size)
        assertEquals(98, result[0].percent)
    }

    @Test
    fun dedupeSportSessionsByDateAndStartSeconds() {
        val existing = listOf(
            SportSessionEntity("2026-10-13", 27000L, 28800L, 1800L, 0, 120, 250, 3000, 0, 0)
        )
        val incoming = listOf(
            SportSessionEntity("2026-10-13", 27000L, 28800L, 1800L, 0, 122, 260, 3000, 0, 0),
            SportSessionEntity("2026-10-13", 36000L, 37800L, 1800L, 3, 130, 300, 5000, 0, 0)
        )

        val result = HealthDeduplicator.dedupeSportSessions(existing, incoming)
        assertEquals(2, result.size)
        assertEquals(122, result[0].heartRate)
        assertEquals(260L, result[0].calorieCal)
        assertEquals(36000L, result[1].startSeconds)
    }
}
