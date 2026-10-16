package rewatch.c900.app

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView

/**
 * Settings screen for notification forwarding.
 * Controls "push other apps" (off by default) and per-type on/off switches,
 * persisted in [android.content.SharedPreferences].
 *
 * Plain Views without external UI libraries.
 */
class SettingsActivity : Activity() {

    lateinit var settings: NotificationSettings
        private set

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        settings = NotificationSettings.fromContext(this)
        val root = createViewHierarchy()
        setContentView(root)
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
            text = "reWatch — Settings"
            textSize = 20f
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 24)
        }
        container.addView(title)

        // "Push other apps" section
        val otherAppsTitle = TextView(this).apply {
            text = "General Push"
            textSize = 16f
            setPadding(0, 8, 0, 8)
        }
        container.addView(otherAppsTitle)

        val otherSwitch = Switch(this).apply {
            text = "Push other (unmapped) apps"
            isChecked = settings.pushOtherApps
            setOnCheckedChangeListener { _, isChecked ->
                settings.pushOtherApps = isChecked
            }
            setPadding(0, 8, 0, 16)
        }
        container.addView(otherSwitch)

        val otherDesc = TextView(this).apply {
            text = "When off, unmapped notifications are dropped (vendor default) to prevent write budget flood."
            textSize = 12f
            setPadding(0, 0, 0, 24)
        }
        container.addView(otherDesc)

        // Per-type on/off section
        val categoriesTitle = TextView(this).apply {
            text = "App Categories"
            textSize = 16f
            setPadding(0, 8, 0, 8)
        }
        container.addView(categoriesTitle)

        for ((type, label) in NotificationSettings.KNOWN_TYPES) {
            val typeSwitch = Switch(this).apply {
                text = label
                isChecked = settings.isTypeEnabled(type)
                setOnCheckedChangeListener { _, isChecked ->
                    settings.setTypeEnabled(type, isChecked)
                }
                setPadding(0, 12, 0, 12)
            }
            container.addView(typeSwitch)
        }

        val closeButton = Button(this).apply {
            text = "Close"
            setOnClickListener { finish() }
            setPadding(0, 24, 0, 16)
        }
        container.addView(closeButton)

        return scrollView
    }
}
