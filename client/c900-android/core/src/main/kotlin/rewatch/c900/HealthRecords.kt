package rewatch.c900

typealias DayTotal = HealthSync.DayTotal

/**
 * 2-byte date decoder shared across cmd 5 health records (PROTOCOL 7, C900-Q16, DevBaseDataUtils.getDateBean).
 * year = 2000 + ((b0 & 0x7F) >> 1), month = ((b0 & 1) << 3) | (b1 >> 5), day = b1 & 0x1F.
 * Note: this is not the cmd 2 key 1 time packing (INVARIANTS I-21 / I-36).
 */
data class HealthDate(val year: Int, val month: Int, val day: Int) : Comparable<HealthDate> {
    val iso: String get() = "${year.toString().padStart(4, '0')}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}"

    override fun compareTo(other: HealthDate): Int {
        val y = year.compareTo(other.year)
        if (y != 0) return y
        val m = month.compareTo(other.month)
        if (m != 0) return m
        return day.compareTo(other.day)
    }

    companion object {
        fun parse(b: ByteArray, offset: Int = 0): HealthDate? {
            if (b.size < offset + 2) return null
            val b0 = b[offset].toInt() and 0xFF
            val b1 = b[offset + 1].toInt() and 0xFF
            val year = 2000 + ((b0 and 0x7F) shr 1)
            val month = ((b0 and 1) shl 3) or (b1 shr 5)
            val day = b1 and 0x1F
            if (month !in 1..12 || day !in 1..31) return null
            return HealthDate(year, month, day)
        }
    }
}

internal fun u16(b: ByteArray, offset: Int): Int {
    if (b.size < offset + 2) return 0
    return ((b[offset].toInt() and 0xFF) shl 8) or (b[offset + 1].toInt() and 0xFF)
}

internal fun u32(b: ByteArray, offset: Int): Long {
    if (b.size < offset + 4) return 0L
    return (0 until 4).fold(0L) { acc, i -> (acc shl 8) or (b[offset + i].toLong() and 0xFF) }
}

/**
 * Key 2 hourly steps: 24 x 8 B records covering 24 hours (StepUtils.getSportBy1Hour, C900-Q16).
 * Payload: 2 B date + 24 * 8 B = 194 B.
 * 0xFFFF in steps indicates no data for that hour.
 * Units [C]: distance in meters, calorie in cal (HistoryStepAdapter.getView).
 * Clamp [C]: steps > 20000 sets steps = distance = 20000, calorie = 400000.
 */
data class HourlyStepRecord(
    val hour: Int,          // 0..23
    val steps: Int,
    val distanceM: Int,     // meters [C]
    val calorieCal: Long    // calories [C]
) {
    val km get() = distanceM / 1000.0
    val kcal get() = calorieCal / 1000.0
}

data class HourlySteps(
    val date: HealthDate,
    val records: List<HourlyStepRecord>
) {
    companion object {
        const val KEY = 2

        fun parse(p: ByteArray): HourlySteps? = try {
            if (p.size < 194) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val records = mutableListOf<HourlyStepRecord>()
                for (i in 0 until 24) {
                    val offset = 2 + 8 * i
                    val rawSteps = u16(p, offset)
                    if (rawSteps == 0xFFFF) continue // none
                    val rawDist = u16(p, offset + 2)
                    val rawCal = u32(p, offset + 4)
                    val steps = if (rawSteps > 20000) 20000 else rawSteps
                    val dist = if (rawSteps > 20000) 20000 else rawDist
                    val cal = if (rawSteps > 20000) 400000L else rawCal
                    records.add(HourlyStepRecord(i, steps, dist, cal))
                }
                HourlySteps(date, records)
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 4 heart rate: records at 4 + 8i (HrUtils.getHrDataList, C900-Q16).
 * Stride 8: u32 seconds of day, 1 B rawType [U], 2 B unread, 1 B bpm.
 * Filter [C]: kept only if bpm in 40..160.
 */
data class HeartRateRecord(
    val secondsOfDay: Long,
    val rawType: Int,       // type byte meaning [U]
    val bpm: Int            // kept if 40..160 [C smali]
) {
    val hour: Int get() = ((secondsOfDay / 3600) % 24).toInt()
    val minute: Int get() = ((secondsOfDay / 60) % 60).toInt()
    val second: Int get() = (secondsOfDay % 60).toInt()
    val timeString: String get() = "${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:${second.toString().padStart(2, '0')}"
}

data class HeartRate(
    val date: HealthDate,
    val records: List<HeartRateRecord>
) {
    companion object {
        const val KEY = 4

        fun parse(p: ByteArray): HeartRate? = try {
            if (p.size < 4) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val count = p[3].toInt() and 0xFF
                if (p.size < 4 + 8 * count) null
                else {
                    val records = mutableListOf<HeartRateRecord>()
                    for (i in 0 until count) {
                        val offset = 4 + 8 * i
                        val seconds = u32(p, offset)
                        val rawType = p[offset + 4].toInt() and 0xFF
                        val bpm = p[offset + 7].toInt() and 0xFF
                        if (bpm in 40..160) {
                            records.add(HeartRateRecord(seconds, rawType, bpm))
                        }
                    }
                    HeartRate(date, records)
                }
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 5 blood pressure: records at 4 + 8i (DevBaseDataUtils.getBloodBean, C900-Q16).
 * Stride 8: u32 seconds of day, 2 B unread, 1 B systolic, 1 B diastolic.
 * Filter [C]: kept if systolic in 50..300 and diastolic in 30..200.
 */
data class BloodPressureRecord(
    val secondsOfDay: Long,
    val systolic: Int,      // kept if 50..300 [C smali]
    val diastolic: Int      // kept if 30..200 [C smali]
) {
    val hour: Int get() = ((secondsOfDay / 3600) % 24).toInt()
    val minute: Int get() = ((secondsOfDay / 60) % 60).toInt()
    val second: Int get() = (secondsOfDay % 60).toInt()
    val timeString: String get() = "${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:${second.toString().padStart(2, '0')}"
}

data class BloodPressure(
    val date: HealthDate,
    val records: List<BloodPressureRecord>
) {
    companion object {
        const val KEY = 5

        fun parse(p: ByteArray): BloodPressure? = try {
            if (p.size < 4) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val count = p[3].toInt() and 0xFF
                if (p.size < 4 + 8 * count) null
                else {
                    val records = mutableListOf<BloodPressureRecord>()
                    for (i in 0 until count) {
                        val offset = 4 + 8 * i
                        val seconds = u32(p, offset)
                        val systolic = p[offset + 6].toInt() and 0xFF
                        val diastolic = p[offset + 7].toInt() and 0xFF
                        if (systolic in 50..300 && diastolic in 30..200) {
                            records.add(BloodPressureRecord(seconds, systolic, diastolic))
                        }
                    }
                    BloodPressure(date, records)
                }
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 9 sleep summary (SleepUtils.receiveTotalSleepData, C900-Q16).
 * Single 12-byte summary frame: date (2 B), start (u16), light (u16), deep (u16), end (u16), awake (u16).
 * Bound [C]: light, deep or awake > 1439 sets all three to 0.
 */
data class SleepSummary(
    val date: HealthDate,
    val startOffsetMinutes: Int,
    val lightMinutes: Int,
    val deepMinutes: Int,
    val endOffsetMinutes: Int,
    val awakeMinutes: Int
) {
    val totalSleepMinutes get() = lightMinutes + deepMinutes

    companion object {
        const val KEY = 9

        fun parse(p: ByteArray): SleepSummary? = try {
            if (p.size < 12) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val start = u16(p, 2)
                var light = u16(p, 4)
                var deep = u16(p, 6)
                val end = u16(p, 8)
                var awake = u16(p, 10)
                if (light > 1439 || deep > 1439 || awake > 1439) {
                    light = 0
                    deep = 0
                    awake = 0
                }
                SleepSummary(date, start, light, deep, end, awake)
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 13 temperature: records at 4 + 8i (TempUtils.getTempDataList, C900-Q16).
 * Stride 8: u32 seconds of day, 1 B rawType [U], 1 B unread, 1 B unsigned degrees, 1 B signed tenths.
 * Formula: value = degrees + (tenths / 10.0). Kept if 30.0..50.0 (Celsius [I]).
 */
data class TemperatureRecord(
    val secondsOfDay: Long,
    val rawType: Int,           // type byte meaning [U]
    val degrees: Int,           // unsigned integer degrees [C smali]
    val tenths: Int,            // signed tenths byte [C smali]
    val temperatureC: Double    // degrees + (tenths / 10.0)
) {
    val hour: Int get() = ((secondsOfDay / 3600) % 24).toInt()
    val minute: Int get() = ((secondsOfDay / 60) % 60).toInt()
    val second: Int get() = (secondsOfDay % 60).toInt()
    val timeString: String get() = "${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:${second.toString().padStart(2, '0')}"
}

data class Temperature(
    val date: HealthDate,
    val records: List<TemperatureRecord>
) {
    companion object {
        const val KEY = 13

        fun parse(p: ByteArray): Temperature? = try {
            if (p.size < 4) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val count = p[3].toInt() and 0xFF
                if (p.size < 4 + 8 * count) null
                else {
                    val records = mutableListOf<TemperatureRecord>()
                    for (i in 0 until count) {
                        val offset = 4 + 8 * i
                        val seconds = u32(p, offset)
                        val rawType = p[offset + 4].toInt() and 0xFF
                        val deg = p[offset + 6].toInt() and 0xFF
                        val tenths = p[offset + 7].toInt() // signed byte
                        val temp = deg.toDouble() + (tenths / 10.0)
                        if (temp in 30.0..50.0) {
                            records.add(TemperatureRecord(seconds, rawType, deg, tenths, temp))
                        }
                    }
                    Temperature(date, records)
                }
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 14 SpO2: inline in HealthUtils.analusis (PROTOCOL 7.2, C900-Q16).
 * Offsets: p[0..1] date, p[4..7] u32 seconds of day, p[11] percent.
 */
data class SpO2Record(
    val date: HealthDate,
    val secondsOfDay: Long,
    val percent: Int            // percentage 0..100 [C smali]
) {
    val hour: Int get() = ((secondsOfDay / 3600) % 24).toInt()
    val minute: Int get() = ((secondsOfDay / 60) % 60).toInt()
    val second: Int get() = (secondsOfDay % 60).toInt()
    val timeString: String get() = "${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:${second.toString().padStart(2, '0')}"

    companion object {
        const val KEY = 14

        fun parse(p: ByteArray): SpO2Record? = try {
            if (p.size < 12) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val seconds = u32(p, 4)
                val percent = p[11].toInt() and 0xFF
                if (percent !in 0..100) null
                else SpO2Record(date, seconds, percent)
            }
        } catch (_: Throwable) {
            null
        }
    }
}

/**
 * Key 15 sport sessions: records at 4 + 30i, stride 30 (DevBaseDataUtils.getSportModeData, C900-Q16).
 * Payload: 2 B date, 1 B unread, 1 B count.
 * Record: start (u32), end (u32), duration (u32), mode (signed byte), hr (signed byte),
 * calorie (u32), rawModeData1..3 (3 x u32).
 * Units [C]: calorie in cal.
 */
data class SportSessionRecord(
    val startSecondsOfDay: Long,
    val endSecondsOfDay: Long,
    val durationSeconds: Long,
    val mode: Int,              // 0 run, 1 rope skipping, 2 sit-ups, 3 cycling [C smali]
    val heartRate: Int,         // signed byte in app [C smali]
    val calorieCal: Long,       // calories [C]
    val rawModeData1: Long,     // mode data 1 meaning per mode [U]
    val rawModeData2: Long,     // mode data 2 meaning per mode [U]
    val rawModeData3: Long      // mode data 3 meaning per mode [U]
) {
    val kcal get() = calorieCal / 1000.0
    val startHour: Int get() = ((startSecondsOfDay / 3600) % 24).toInt()
    val startMinute: Int get() = ((startSecondsOfDay / 60) % 60).toInt()
    val startSecond: Int get() = (startSecondsOfDay % 60).toInt()
    val startTimeString: String get() = "${startHour.toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}:${startSecond.toString().padStart(2, '0')}"
}

data class SportSessions(
    val date: HealthDate,
    val records: List<SportSessionRecord>
) {
    companion object {
        const val KEY = 15

        fun parse(p: ByteArray): SportSessions? = try {
            if (p.size < 4) null
            else {
                val date = HealthDate.parse(p, 0) ?: return null
                val count = p[3].toInt() and 0xFF
                if (p.size < 4 + 30 * count) null
                else {
                    val records = mutableListOf<SportSessionRecord>()
                    for (i in 0 until count) {
                        val offset = 4 + 30 * i
                        val start = u32(p, offset)
                        val end = u32(p, offset + 4)
                        val duration = u32(p, offset + 8)
                        val mode = p[offset + 12].toInt()
                        val hr = p[offset + 13].toInt()
                        val calorie = u32(p, offset + 14)
                        val raw1 = u32(p, offset + 18)
                        val raw2 = u32(p, offset + 22)
                        val raw3 = u32(p, offset + 26)
                        records.add(SportSessionRecord(start, end, duration, mode, hr, calorie, raw1, raw2, raw3))
                    }
                    SportSessions(date, records)
                }
            }
        } catch (_: Throwable) {
            null
        }
    }
}
