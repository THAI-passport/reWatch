package rewatch.c900

import kotlin.test.*
import java.util.Random

class HealthParsersTest {

    // Helper to build 2-byte date: year 2026, month 10, day 13 -> 0x35, 0x4D
    private val date20261013 = byteArrayOf(0x35, 0x4D)

    @Test
    fun dateDecoder() {
        // Own arithmetic, not a capture:
        // year 2026: (2026 - 2000) = 26. (26 << 1) = 52 = 0x34.
        // month 10: high bit (10 >> 3) = 1 -> b0 bit 0 = 1. b0 = 0x34 | 1 = 0x35.
        // low 3 bits (10 & 7) = 2 -> (2 << 5) = 64 = 0x40.
        // day 13 = 0x0D. b1 = 0x40 | 0x0D = 0x4D.
        val d = HealthDate.parse(date20261013)
        assertNotNull(d)
        assertEquals(2026, d!!.year)
        assertEquals(10, d.month)
        assertEquals(13, d.day)
        assertEquals("2026-10-13", d.iso)

        // Short date
        assertNull(HealthDate.parse(byteArrayOf(0x35)))
        // Invalid month 0 or 13
        assertNull(HealthDate.parse(byteArrayOf(0x34, 0x0D))) // month = 0
        assertNull(HealthDate.parse(byteArrayOf(0x35, 0xFD.toByte()))) // month = 15
    }

    @Test
    fun key2HourlyStepsVector() {
        // Own arithmetic, not a capture.
        // 194 bytes: 2 B date + 24 x 8 B. Hour 7 has 1200 steps, 850 m, 45 cal. Others 0xFFFF.
        val p = ByteArray(194)
        p[0] = 0x35; p[1] = 0x4D
        for (i in 0 until 24) {
            val off = 2 + 8 * i
            if (i == 7) {
                // 1200 steps = 0x04B0, 850 m = 0x0352, 45 cal = 0x0000002D
                p[off] = 0x04; p[off + 1] = 0xB0.toByte()
                p[off + 2] = 0x03; p[off + 3] = 0x52
                p[off + 4] = 0; p[off + 5] = 0; p[off + 6] = 0; p[off + 7] = 0x2D
            } else {
                p[off] = 0xFF.toByte(); p[off + 1] = 0xFF.toByte()
            }
        }
        val s = HourlySteps.parse(p)
        assertNotNull(s)
        assertEquals("2026-10-13", s!!.date.iso)
        assertEquals(1, s.records.size)
        val r = s.records[0]
        assertEquals(7, r.hour)
        assertEquals(1200, r.steps)
        assertEquals(850, r.distanceM)
        assertEquals(45L, r.calorieCal)
        assertEquals(0.85, r.km, 1e-6)
        assertEquals(0.045, r.kcal, 1e-6)

        // Clamping test: steps > 20000 sets steps=20000, distance=20000, cal=400000
        p[2 + 8 * 7] = 0x61; p[2 + 8 * 7 + 1] = 0xA8.toByte() // 25000
        val clamped = HourlySteps.parse(p)!!.records[0]
        assertEquals(20000, clamped.steps)
        assertEquals(20000, clamped.distanceM)
        assertEquals(400000L, clamped.calorieCal)

        // Short payload returns null
        assertNull(HourlySteps.parse(ByteArray(193)))
    }

    @Test
    fun key4HeartRateVector() {
        // Own arithmetic, not a capture.
        // 12 bytes: date 2 B, unread 1 B, count 1 B, 1 record of 8 B.
        // seconds 27000 (07:30:00 = 0x00006978), rawType 1, unread 2 B, bpm 72 (0x48).
        val p = byteArrayOf(
            0x35, 0x4D, 0x00, 0x01,
            0x00, 0x00, 0x69, 0x78,
            0x01, 0x00, 0x00, 0x48
        )
        val hr = HeartRate.parse(p)
        assertNotNull(hr)
        assertEquals("2026-10-13", hr!!.date.iso)
        assertEquals(1, hr.records.size)
        val r = hr.records[0]
        assertEquals(27000L, r.secondsOfDay)
        assertEquals(7, r.hour)
        assertEquals(30, r.minute)
        assertEquals(0, r.second)
        assertEquals("07:30:00", r.timeString)
        assertEquals(1, r.rawType)
        assertEquals(72, r.bpm)

        // Filter: bpm < 40 or > 160 is dropped
        val pLow = p.clone().also { it[11] = 39 }
        assertEquals(0, HeartRate.parse(pLow)!!.records.size)
        val pHigh = p.clone().also { it[11] = 161.toByte() }
        assertEquals(0, HeartRate.parse(pHigh)!!.records.size)

        // Short payload
        assertNull(HeartRate.parse(byteArrayOf(0x35, 0x4D, 0x00)))
        assertNull(HeartRate.parse(byteArrayOf(0x35, 0x4D, 0x00, 0x01, 0x00)))
    }

    @Test
    fun key5BloodPressureVector() {
        // Own arithmetic, not a capture.
        // 12 bytes: date 2 B, unread 1 B, count 1 B, 1 record of 8 B.
        // seconds 27000 (0x00006978), unread 2 B, systolic 118 (0x76), diastolic 76 (0x4C).
        val p = byteArrayOf(
            0x35, 0x4D, 0x00, 0x01,
            0x00, 0x00, 0x69, 0x78,
            0x00, 0x00, 0x76, 0x4C
        )
        val bp = BloodPressure.parse(p)
        assertNotNull(bp)
        assertEquals("2026-10-13", bp!!.date.iso)
        assertEquals(1, bp.records.size)
        val r = bp.records[0]
        assertEquals(27000L, r.secondsOfDay)
        assertEquals("07:30:00", r.timeString)
        assertEquals(118, r.systolic)
        assertEquals(76, r.diastolic)

        // Filter: systolic 40 (< 50) dropped
        val pLowSys = p.clone().also { it[10] = 49 }
        assertEquals(0, BloodPressure.parse(pLowSys)!!.records.size)
        // Filter: diastolic 25 (< 30) dropped
        val pLowDia = p.clone().also { it[11] = 29 }
        assertEquals(0, BloodPressure.parse(pLowDia)!!.records.size)

        assertNull(BloodPressure.parse(ByteArray(11)))
    }

    @Test
    fun key9SleepSummaryVector() {
        // Own arithmetic, not a capture.
        // 12 bytes: date 2 B, start 1380 (0x0564), light 240 (0x00F0), deep 120 (0x0078), end 420 (0x01A4), awake 15 (0x000F).
        val p = byteArrayOf(
            0x35, 0x4D,
            0x05, 0x64,
            0x00, 0xF0.toByte(),
            0x00, 0x78,
            0x01, 0xA4.toByte(),
            0x00, 0x0F
        )
        val s = SleepSummary.parse(p)
        assertNotNull(s)
        assertEquals("2026-10-13", s!!.date.iso)
        assertEquals(1380, s.startOffsetMinutes)
        assertEquals(240, s.lightMinutes)
        assertEquals(120, s.deepMinutes)
        assertEquals(420, s.endOffsetMinutes)
        assertEquals(15, s.awakeMinutes)
        assertEquals(360, s.totalSleepMinutes)

        // Bound: light > 1439 resets light, deep, awake to 0
        val pOversleep = p.clone().also { it[4] = 0x06; it[5] = 0x00 } // 1536
        val sOver = SleepSummary.parse(pOversleep)!!
        assertEquals(0, sOver.lightMinutes)
        assertEquals(0, sOver.deepMinutes)
        assertEquals(0, sOver.awakeMinutes)

        assertNull(SleepSummary.parse(ByteArray(11)))
    }

    @Test
    fun key12DayTotalVector() {
        // Own arithmetic, not a capture.
        // 12 bytes: steps 8000 (0x00001F40), dist 5600 m (0x000015E0), cal 320 cal (0x00000140).
        val p = byteArrayOf(
            0x00, 0x00, 0x1F, 0x40,
            0x00, 0x00, 0x15, 0xE0.toByte(),
            0x00, 0x00, 0x01, 0x40
        )
        val t = DayTotal.parse(p)
        assertNotNull(t)
        assertEquals(8000L, t!!.steps)
        assertEquals(5600L, t.distanceM)
        assertEquals(320L, t.calorieCal)
        assertEquals(5.6, t.km, 1e-6)
        assertEquals(0.32, t.kcal, 1e-6)

        // Bound: steps > 240000 resets all 3 to 0
        val pOverflow = byteArrayOf(
            0x00, 0x04, 0x00, 0x00, // 262144
            0x00, 0x00, 0x15, 0xE0.toByte(),
            0x00, 0x00, 0x01, 0x40
        )
        val tOver = DayTotal.parse(pOverflow)!!
        assertEquals(0L, tOver.steps)
        assertEquals(0L, tOver.distanceM)
        assertEquals(0L, tOver.calorieCal)

        assertNull(DayTotal.parse(ByteArray(11)))
    }

    @Test
    fun key13TemperatureVector() {
        // Own arithmetic, not a capture.
        // 12 bytes: date 2 B, unread 1 B, count 1 B, 1 record of 8 B.
        // seconds 27000 (0x00006978), rawType 1, unread 1 B, deg 36 (0x24), tenths 6 (0x06) -> 36.6 C.
        val p = byteArrayOf(
            0x35, 0x4D, 0x00, 0x01,
            0x00, 0x00, 0x69, 0x78,
            0x01, 0x00, 0x24, 0x06
        )
        val t = Temperature.parse(p)
        assertNotNull(t)
        assertEquals("2026-10-13", t!!.date.iso)
        assertEquals(1, t.records.size)
        val r = t.records[0]
        assertEquals(27000L, r.secondsOfDay)
        assertEquals("07:30:00", r.timeString)
        assertEquals(1, r.rawType)
        assertEquals(36, r.degrees)
        assertEquals(6, r.tenths)
        assertEquals(36.6, r.temperatureC, 1e-6)

        // Signed tenths: deg 37, tenths -4 (0xFC) -> 36.6 C
        val pNegTenths = p.clone().also { it[10] = 0x25; it[11] = 0xFC.toByte() }
        val rNeg = Temperature.parse(pNegTenths)!!.records[0]
        assertEquals(36.6, rNeg.temperatureC, 1e-6)

        // Filter: outside 30.0..50.0 dropped
        val pLow = p.clone().also { it[10] = 0x18 } // 24 C
        assertEquals(0, Temperature.parse(pLow)!!.records.size)

        assertNull(Temperature.parse(ByteArray(11)))
    }

    @Test
    fun key14SpO2Vector() {
        // Own arithmetic, not a capture.
        // 12 bytes: date 2 B, unread 2 B, seconds 27000 (0x00006978), unread 3 B, percent 98 (0x62).
        val p = byteArrayOf(
            0x35, 0x4D, 0x00, 0x00,
            0x00, 0x00, 0x69, 0x78,
            0x00, 0x00, 0x00, 0x62
        )
        val sp = SpO2Record.parse(p)
        assertNotNull(sp)
        assertEquals("2026-10-13", sp!!.date.iso)
        assertEquals(27000L, sp.secondsOfDay)
        assertEquals("07:30:00", sp.timeString)
        assertEquals(98, sp.percent)

        // Invalid percentage > 100
        val pBad = p.clone().also { it[11] = 101.toByte() }
        assertNull(SpO2Record.parse(pBad))

        assertNull(SpO2Record.parse(ByteArray(11)))
    }

    @Test
    fun key15SportSessionsVector() {
        // Own arithmetic, not a capture.
        // 34 bytes: date 2 B, unread 1 B, count 1 B, 1 record of 30 B.
        // start 27000, end 28800, duration 1800, mode 0 (run), hr 120, calorie 250 cal, raw1 3000, raw2 0, raw3 0.
        val p = ByteArray(34)
        p[0] = 0x35; p[1] = 0x4D; p[2] = 0; p[3] = 1
        // start 27000 = 0x00006978
        p[4] = 0; p[5] = 0; p[6] = 0x69; p[7] = 0x78
        // end 28800 = 0x00007080
        p[8] = 0; p[9] = 0; p[10] = 0x70; p[11] = 0x80.toByte()
        // duration 1800 = 0x00000708
        p[12] = 0; p[13] = 0; p[14] = 0x07; p[15] = 0x08
        // mode 0, hr 120 (0x78)
        p[16] = 0; p[17] = 0x78
        // calorie 250 = 0x000000FA
        p[18] = 0; p[19] = 0; p[20] = 0; p[21] = 0xFA.toByte()
        // raw1 3000 = 0x00000BB8
        p[22] = 0; p[23] = 0; p[24] = 0x0B; p[25] = 0xB8.toByte()
        // raw2 = 0 (26..29), raw3 = 0 (30..33)

        val sp = SportSessions.parse(p)
        assertNotNull(sp)
        assertEquals("2026-10-13", sp!!.date.iso)
        assertEquals(1, sp.records.size)
        val r = sp.records[0]
        assertEquals(27000L, r.startSecondsOfDay)
        assertEquals(28800L, r.endSecondsOfDay)
        assertEquals(1800L, r.durationSeconds)
        assertEquals(0, r.mode)
        assertEquals(120, r.heartRate)
        assertEquals(250L, r.calorieCal)
        assertEquals(0.25, r.kcal, 1e-6)
        assertEquals(3000L, r.rawModeData1)
        assertEquals(0L, r.rawModeData2)
        assertEquals(0L, r.rawModeData3)

        assertNull(SportSessions.parse(ByteArray(33)))
    }

    @Test
    fun fuzzParsersNeverThrowOnRandomBytes() {
        val rng = Random(42)
        for (i in 0 until 500) {
            val len = rng.nextInt(300)
            val bytes = ByteArray(len).also { rng.nextBytes(it) }
            // Must return null or valid record without throwing
            HealthDate.parse(bytes)
            HourlySteps.parse(bytes)
            HeartRate.parse(bytes)
            BloodPressure.parse(bytes)
            SleepSummary.parse(bytes)
            DayTotal.parse(bytes)
            Temperature.parse(bytes)
            SpO2Record.parse(bytes)
            SportSessions.parse(bytes)
        }
    }
}
