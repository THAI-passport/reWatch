package rewatch.c900.app

import android.app.Activity
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import rewatch.c900.CommandQueue
import rewatch.c900.HealthSync
import rewatch.c900.Session
import java.util.Locale

/**
 * Single day summary item for last 7 days display.
 */
data class DayHistoryItem(
    val date: String,
    val steps: Long,
    val distanceKm: String,
    val caloriesKcal: String
) {
    val displayText get() = "$date: $steps steps, $distanceKm, $caloriesKcal"
}

/**
 * Snapshot model of watch status displayed on the status screen.
 * Formatted cleanly for display and unit-testable without Android framework dependencies.
 */
data class StatusSnapshot(
    val connectionState: String,
    val battery: String,
    val version: String,
    val distanceKm: String,
    val caloriesKcal: String,
    val writesBudget: String,
    val historyLast7Days: List<DayHistoryItem> = emptyList()
) {
    companion object {
        const val MAX_BUDGET = 200 // Ground rule 7 session write budget

        fun from(service: WatchService?, storage: HealthStorage? = null): StatusSnapshot {
            val history = try {
                storage?.getLast7DaysSummaries()
            } catch (_: Throwable) {
                null
            }
            if (service == null) {
                val histItems = history?.map {
                    DayHistoryItem(
                        date = it.date,
                        steps = it.steps,
                        distanceKm = "%.2f km".format(Locale.US, it.km),
                        caloriesKcal = "%.2f kcal".format(Locale.US, it.kcal)
                    )
                } ?: emptyList()
                return StatusSnapshot(
                    connectionState = "Service not running",
                    battery = "—",
                    version = "—",
                    distanceKm = "—",
                    caloriesKcal = "—",
                    writesBudget = "0 / $MAX_BUDGET",
                    historyLast7Days = histItems
                )
            }
            return format(service.session, service.healthSync, service.commandQueue, history)
        }

        fun format(
            session: Session?,
            healthSync: HealthSync?,
            commandQueue: CommandQueue?,
            history: List<HealthStorage.DaySummary>? = null
        ): StatusSnapshot {
            val stateStr = when (session?.state) {
                Session.State.READY -> "Connected (Ready)"
                Session.State.CONNECTING -> "Connecting..."
                Session.State.DISCOVERING -> "Discovering Services..."
                Session.State.READING_INFO -> "Reading Device Info..."
                Session.State.DISCONNECTED -> "Disconnected"
                Session.State.ERROR -> "Error"
                Session.State.IDLE -> "Idle"
                null -> "Disconnected"
            }

            val batteryStr = session?.battery?.let { "$it%" } ?: "—"
            val verStr = session?.ver?.let { "0x%02X".format(Locale.US, it) } ?: "—"

            val dt = healthSync?.dayTotal
            val distStr = dt?.let { "%.2f km".format(Locale.US, it.km) } ?: "—"
            val calStr = dt?.let { "%.2f kcal".format(Locale.US, it.kcal) } ?: "—"

            val writes = commandQueue?.writes ?: 0
            val writesStr = "$writes / $MAX_BUDGET"

            val historyItems = history?.map {
                DayHistoryItem(
                    date = it.date,
                    steps = it.steps,
                    distanceKm = "%.2f km".format(Locale.US, it.km),
                    caloriesKcal = "%.2f kcal".format(Locale.US, it.kcal)
                )
            } ?: emptyList()

            return StatusSnapshot(
                connectionState = stateStr,
                battery = batteryStr,
                version = verStr,
                distanceKm = distStr,
                caloriesKcal = calStr,
                writesBudget = writesStr,
                historyLast7Days = historyItems
            )
        }
    }
}

/**
 * Status screen displaying live watch telemetry and local history:
 * - Connection state (Session.state)
 * - Battery percentage (Session.battery)
 * - Protocol version (Session.ver)
 * - Last HealthSync day totals (km, kcal)
 * - Session write counter (CommandQueue.writes of the 200 budget)
 * - Last 7 days of steps, distance (km), kcal from local storage (HealthStorage)
 *
 * Plain Views without external UI libraries.
 */
class StatusActivity : Activity() {

    private val handler = Handler(Looper.getMainLooper())
    private var isResumed = false

    private lateinit var healthStorage: HealthStorage
    private lateinit var stateView: TextView
    private lateinit var batteryView: TextView
    private lateinit var verView: TextView
    private lateinit var distanceView: TextView
    private lateinit var caloriesView: TextView
    private lateinit var writesView: TextView
    private lateinit var historyContainer: LinearLayout

    private val refreshRunnable = object : Runnable {
        override fun run() {
            if (!isResumed) return
            updateViews()
            handler.postDelayed(this, REFRESH_INTERVAL_MS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        healthStorage = HealthStorage(this)
        val root = createViewHierarchy()
        setContentView(root)
    }

    override fun onResume() {
        super.onResume()
        isResumed = true
        updateViews()
        handler.postDelayed(refreshRunnable, REFRESH_INTERVAL_MS)
    }

    override fun onPause() {
        isResumed = false
        handler.removeCallbacks(refreshRunnable)
        super.onPause()
    }

    override fun onDestroy() {
        if (::healthStorage.isInitialized) {
            healthStorage.close()
        }
        super.onDestroy()
    }

    fun updateViews() {
        val snapshot = StatusSnapshot.from(WatchService.activeInstance, healthStorage)
        stateView.text = snapshot.connectionState
        batteryView.text = snapshot.battery
        verView.text = snapshot.version
        distanceView.text = snapshot.distanceKm
        caloriesView.text = snapshot.caloriesKcal
        writesView.text = snapshot.writesBudget

        // Render last 7 days history
        historyContainer.removeAllViews()
        if (snapshot.historyLast7Days.isEmpty()) {
            val emptyView = TextView(this).apply {
                text = "No history records stored yet."
                textSize = 13f
                setPadding(0, 4, 0, 8)
            }
            historyContainer.addView(emptyView)
        } else {
            for (item in snapshot.historyLast7Days) {
                val row = TextView(this).apply {
                    text = "${item.date}: ${item.steps} steps  |  ${item.distanceKm}  |  ${item.caloriesKcal}"
                    textSize = 13f
                    setPadding(0, 4, 0, 4)
                }
                historyContainer.addView(row)
            }
        }
    }

    private fun createViewHierarchy(): View {
        val scrollView = ScrollView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 48, 32, 48)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }
        scrollView.addView(container)

        val title = TextView(this).apply {
            text = "reWatch — Watch Status"
            textSize = 20f
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 24)
        }
        container.addView(title)

        // Connection State
        container.addView(createSectionHeader("Connection"))
        stateView = createValueRow(container, "State:")

        // Device Info
        container.addView(createSectionHeader("Device Telemetry"))
        batteryView = createValueRow(container, "Battery:")
        verView = createValueRow(container, "Protocol Ver:")

        // Health Day Totals
        container.addView(createSectionHeader("Health Day Totals (cmd 5 key 12)"))
        distanceView = createValueRow(container, "Distance:")
        caloriesView = createValueRow(container, "Calories:")

        // Last 7 Days History
        container.addView(createSectionHeader("Last 7 Days (Local Storage)"))
        historyContainer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 4, 0, 16)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }
        container.addView(historyContainer)

        // Session Write Budget
        container.addView(createSectionHeader("Session Write Budget"))
        writesView = createValueRow(container, "Writes (pieces):")
        val budgetNote = TextView(this).apply {
            text = "Enforces safe write budget (max 200 writes/session) to protect watch flash."
            textSize = 12f
            setPadding(0, 4, 0, 24)
        }
        container.addView(budgetNote)

        // Actions: one tap = one command (LIVE-APP-1 steps 4-5); ignored unless connected and ready.
        container.addView(Button(this).apply {
            text = "Find watch (1 write)"
            setOnClickListener { WatchService.activeInstance?.sendFind() }
        })
        container.addView(Button(this).apply {
            text = "Sync time (1 write)"
            setOnClickListener { WatchService.activeInstance?.sendTimeSync() }
        })

        val refreshButton = Button(this).apply {
            text = "Refresh Now"
            setOnClickListener { updateViews() }
            setPadding(0, 16, 0, 16)
        }
        container.addView(refreshButton)

        val closeButton = Button(this).apply {
            text = "Close"
            setOnClickListener { finish() }
            setPadding(0, 16, 0, 16)
        }
        container.addView(closeButton)

        return scrollView
    }

    private fun createSectionHeader(title: String): TextView {
        return TextView(this).apply {
            text = title
            textSize = 16f
            setPadding(0, 16, 0, 8)
        }
    }

    private fun createValueRow(parent: ViewGroup, label: String): TextView {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 6, 0, 6)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }

        val labelView = TextView(this).apply {
            text = label
            textSize = 14f
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        row.addView(labelView)

        val valueView = TextView(this).apply {
            text = "—"
            textSize = 14f
            gravity = Gravity.END
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }
        row.addView(valueView)

        parent.addView(row)
        return valueView
    }

    companion object {
        const val REFRESH_INTERVAL_MS = 1000L
    }
}
