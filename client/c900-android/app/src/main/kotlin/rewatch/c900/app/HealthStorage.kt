package rewatch.c900.app

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import rewatch.c900.SyncedHealthData
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Local health record storage using plain android.database.sqlite (no Room, no external dependencies).
 * Enforces composite primary keys per record kind so repeated syncs do not duplicate rows.
 * No network access, no analytics, no external export: all data remains strictly local to the device.
 */
class HealthStorage(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {

    data class DaySummary(
        val date: String,
        val steps: Long,
        val distanceM: Long,
        val calorieCal: Long
    ) {
        val km get() = distanceM / 1000.0
        val kcal get() = calorieCal / 1000.0
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_HOURLY_STEPS (
                date TEXT NOT NULL,
                hour INTEGER NOT NULL,
                steps INTEGER NOT NULL,
                distance_m INTEGER NOT NULL,
                calorie_cal INTEGER NOT NULL,
                PRIMARY KEY (date, hour)
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_HEART_RATE (
                date TEXT NOT NULL,
                seconds_of_day INTEGER NOT NULL,
                raw_type INTEGER NOT NULL,
                bpm INTEGER NOT NULL,
                PRIMARY KEY (date, seconds_of_day)
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_BLOOD_PRESSURE (
                date TEXT NOT NULL,
                seconds_of_day INTEGER NOT NULL,
                systolic INTEGER NOT NULL,
                diastolic INTEGER NOT NULL,
                PRIMARY KEY (date, seconds_of_day)
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_SLEEP_SUMMARY (
                date TEXT NOT NULL PRIMARY KEY,
                start_minutes INTEGER NOT NULL,
                light_minutes INTEGER NOT NULL,
                deep_minutes INTEGER NOT NULL,
                end_minutes INTEGER NOT NULL,
                awake_minutes INTEGER NOT NULL,
                total_sleep_minutes INTEGER NOT NULL
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_DAY_TOTAL (
                date TEXT NOT NULL PRIMARY KEY,
                steps INTEGER NOT NULL,
                distance_m INTEGER NOT NULL,
                calorie_cal INTEGER NOT NULL
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_TEMPERATURE (
                date TEXT NOT NULL,
                seconds_of_day INTEGER NOT NULL,
                raw_type INTEGER NOT NULL,
                degrees INTEGER NOT NULL,
                tenths INTEGER NOT NULL,
                temp_c REAL NOT NULL,
                PRIMARY KEY (date, seconds_of_day)
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_SPO2 (
                date TEXT NOT NULL,
                seconds_of_day INTEGER NOT NULL,
                percent INTEGER NOT NULL,
                PRIMARY KEY (date, seconds_of_day)
            )
        """.trimIndent())

        db.execSQL("""
            CREATE TABLE IF NOT EXISTS $TABLE_SPORT_SESSION (
                date TEXT NOT NULL,
                start_seconds INTEGER NOT NULL,
                end_seconds INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL,
                mode INTEGER NOT NULL,
                heart_rate INTEGER NOT NULL,
                calorie_cal INTEGER NOT NULL,
                raw1 INTEGER NOT NULL,
                raw2 INTEGER NOT NULL,
                raw3 INTEGER NOT NULL,
                PRIMARY KEY (date, start_seconds)
            )
        """.trimIndent())
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // Upgrade policy: when schema changes, alter tables. Version 1 initial release.
    }

    /**
     * Persists all records from a completed sync into SQLite.
     * Uses CONFLICT_REPLACE on composite keys to ensure duplicate records from repeated syncs are updated in place.
     */
    fun saveSync(data: SyncedHealthData) {
        val db = writableDatabase
        db.beginTransaction()
        try {
            // 1. Hourly steps
            for (batch in data.hourlySteps) {
                val dateStr = batch.date.iso
                for (rec in batch.records) {
                    val values = ContentValues().apply {
                        put("date", dateStr)
                        put("hour", rec.hour)
                        put("steps", rec.steps)
                        put("distance_m", rec.distanceM)
                        put("calorie_cal", rec.calorieCal)
                    }
                    db.insertWithOnConflict(TABLE_HOURLY_STEPS, null, values, SQLiteDatabase.CONFLICT_REPLACE)
                }
            }

            // 2. Heart rate
            for (batch in data.heartRates) {
                val dateStr = batch.date.iso
                for (rec in batch.records) {
                    val values = ContentValues().apply {
                        put("date", dateStr)
                        put("seconds_of_day", rec.secondsOfDay)
                        put("raw_type", rec.rawType)
                        put("bpm", rec.bpm)
                    }
                    db.insertWithOnConflict(TABLE_HEART_RATE, null, values, SQLiteDatabase.CONFLICT_REPLACE)
                }
            }

            // 3. Blood pressure
            for (batch in data.bloodPressures) {
                val dateStr = batch.date.iso
                for (rec in batch.records) {
                    val values = ContentValues().apply {
                        put("date", dateStr)
                        put("seconds_of_day", rec.secondsOfDay)
                        put("systolic", rec.systolic)
                        put("diastolic", rec.diastolic)
                    }
                    db.insertWithOnConflict(TABLE_BLOOD_PRESSURE, null, values, SQLiteDatabase.CONFLICT_REPLACE)
                }
            }

            // 4. Sleep summary
            for (rec in data.sleepSummaries) {
                val values = ContentValues().apply {
                    put("date", rec.date.iso)
                    put("start_minutes", rec.startOffsetMinutes)
                    put("light_minutes", rec.lightMinutes)
                    put("deep_minutes", rec.deepMinutes)
                    put("end_minutes", rec.endOffsetMinutes)
                    put("awake_minutes", rec.awakeMinutes)
                    put("total_sleep_minutes", rec.totalSleepMinutes)
                }
                db.insertWithOnConflict(TABLE_SLEEP_SUMMARY, null, values, SQLiteDatabase.CONFLICT_REPLACE)
            }

            // 5. Day total: date comes from hourly steps if present, otherwise today's date
            val total = data.dayTotal
            if (total != null) {
                val totalDate = data.hourlySteps.firstOrNull()?.date?.iso ?: todayIso()
                val values = ContentValues().apply {
                    put("date", totalDate)
                    put("steps", total.steps)
                    put("distance_m", total.distanceM)
                    put("calorie_cal", total.calorieCal)
                }
                db.insertWithOnConflict(TABLE_DAY_TOTAL, null, values, SQLiteDatabase.CONFLICT_REPLACE)
            }

            // 6. Temperature
            for (batch in data.temperatures) {
                val dateStr = batch.date.iso
                for (rec in batch.records) {
                    val values = ContentValues().apply {
                        put("date", dateStr)
                        put("seconds_of_day", rec.secondsOfDay)
                        put("raw_type", rec.rawType)
                        put("degrees", rec.degrees)
                        put("tenths", rec.tenths)
                        put("temp_c", rec.temperatureC)
                    }
                    db.insertWithOnConflict(TABLE_TEMPERATURE, null, values, SQLiteDatabase.CONFLICT_REPLACE)
                }
            }

            // 7. SpO2
            for (rec in data.spo2Records) {
                val values = ContentValues().apply {
                    put("date", rec.date.iso)
                    put("seconds_of_day", rec.secondsOfDay)
                    put("percent", rec.percent)
                }
                db.insertWithOnConflict(TABLE_SPO2, null, values, SQLiteDatabase.CONFLICT_REPLACE)
            }

            // 8. Sport session
            for (batch in data.sportSessions) {
                val dateStr = batch.date.iso
                for (rec in batch.records) {
                    val values = ContentValues().apply {
                        put("date", dateStr)
                        put("start_seconds", rec.startSecondsOfDay)
                        put("end_seconds", rec.endSecondsOfDay)
                        put("duration_seconds", rec.durationSeconds)
                        put("mode", rec.mode)
                        put("heart_rate", rec.heartRate)
                        put("calorie_cal", rec.calorieCal)
                        put("raw1", rec.rawModeData1)
                        put("raw2", rec.rawModeData2)
                        put("raw3", rec.rawModeData3)
                    }
                    db.insertWithOnConflict(TABLE_SPORT_SESSION, null, values, SQLiteDatabase.CONFLICT_REPLACE)
                }
            }

            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }

    /**
     * Retrieves day step summaries for the last 7 days from storage.
     * Combines day_total entries with aggregated hourly_steps entries if day_total is missing.
     */
    fun getLast7DaysSummaries(): List<DaySummary> {
        val result = mutableMapOf<String, DaySummary>()
        val db = readableDatabase

        // 1. Query day_total table (most authoritative day summaries)
        val dayTotalCursor = db.rawQuery(
            "SELECT date, steps, distance_m, calorie_cal FROM $TABLE_DAY_TOTAL ORDER BY date DESC LIMIT 7",
            null
        )
        dayTotalCursor.use { c ->
            while (c.moveToNext()) {
                val date = c.getString(0)
                val steps = c.getLong(1)
                val dist = c.getLong(2)
                val cal = c.getLong(3)
                result[date] = DaySummary(date, steps, dist, cal)
            }
        }

        // 2. Query aggregated hourly_steps for dates not already present in day_total
        val hourlyCursor = db.rawQuery(
            """
            SELECT date, SUM(steps) as total_steps, SUM(distance_m) as total_dist, SUM(calorie_cal) as total_cal
            FROM $TABLE_HOURLY_STEPS
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7
            """.trimIndent(),
            null
        )
        hourlyCursor.use { c ->
            while (c.moveToNext()) {
                val date = c.getString(0)
                if (!result.containsKey(date)) {
                    val steps = c.getLong(1)
                    val dist = c.getLong(2)
                    val cal = c.getLong(3)
                    result[date] = DaySummary(date, steps, dist, cal)
                }
            }
        }

        // Return sorted by date descending, up to 7 items
        return result.values.sortedByDescending { it.date }.take(7)
    }

    private fun todayIso(): String {
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        return sdf.format(Date())
    }

    companion object {
        const val DB_NAME = "health.db"
        const val DB_VERSION = 1

        const val TABLE_HOURLY_STEPS = "hourly_steps"
        const val TABLE_HEART_RATE = "heart_rate"
        const val TABLE_BLOOD_PRESSURE = "blood_pressure"
        const val TABLE_SLEEP_SUMMARY = "sleep_summary"
        const val TABLE_DAY_TOTAL = "day_total"
        const val TABLE_TEMPERATURE = "temperature"
        const val TABLE_SPO2 = "spo2"
        const val TABLE_SPORT_SESSION = "sport_session"
    }
}
