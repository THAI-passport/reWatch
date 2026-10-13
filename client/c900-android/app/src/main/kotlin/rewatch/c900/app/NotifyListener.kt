package rewatch.c900.app

import android.app.Notification
import android.os.SystemClock
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

/**
 * Deduplicator for notification streams.
 * Drops identical (package, title, body) triplets occurring within [windowMs].
 * Vendor dedupes identical text (R04). [windowMs] = 2000 ms is a placeholder [I].
 */
class NotificationDeduplicator(
    private val windowMs: Long = DEDUPE_WINDOW_MS,
    private val nowMs: () -> Long = { SystemClock.elapsedRealtime() }
) {
    private data class Key(val pkg: String, val title: String, val body: String)
    private var lastKey: Key? = null
    private var lastTimeMs = 0L

    @Synchronized
    fun shouldDrop(pkg: String, title: String, body: String): Boolean {
        val now = nowMs()
        val key = Key(pkg, title, body)
        if (key == lastKey && (now - lastTimeMs) < windowMs && lastTimeMs > 0L) {
            return true
        }
        lastKey = key
        lastTimeMs = now
        return false
    }

    @Synchronized
    fun reset() {
        lastKey = null
        lastTimeMs = 0L
    }

    companion object {
        const val DEDUPE_WINDOW_MS = 2000L
    }
}

/**
 * Pure filter logic for notification flags and package origin.
 * Filters ongoing events, group summaries, and own package notifications (ground rule 7).
 */
object NotificationFilter {
    fun shouldFilter(flags: Int, packageName: String?, selfPackageName: String?): Boolean {
        if (packageName.isNullOrBlank()) return true
        if (selfPackageName != null && packageName == selfPackageName) return true
        if ((flags and Notification.FLAG_ONGOING_EVENT) != 0) return true
        if ((flags and Notification.FLAG_GROUP_SUMMARY) != 0) return true
        return false
    }
}

/**
 * NotificationListenerService capturing posted notifications and forwarding them
 * to [WatchService] as cmd 0x02 key 18 message frames.
 *
 * Package mapping uses the new type table (C900-Q04 section 5).
 * Filters ongoing events, group summaries, own package, and drops repeats within 2000 ms.
 * Privacy: notification text, MAC addresses, and device names are never logged.
 */
class NotifyListener : NotificationListenerService() {

    val deduplicator = NotificationDeduplicator()

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        val n = sbn?.notification ?: return
        val pkg = sbn.packageName ?: return

        if (NotificationFilter.shouldFilter(n.flags, pkg, packageName)) return

        val type = NotificationMapper.mapPackage(pkg)
        if (type == NotificationMapper.TYPE_IGNORE) return

        val extras = n.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val body = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""

        if (title.isBlank() && body.isBlank()) return

        if (deduplicator.shouldDrop(pkg, title, body)) return

        val service = WatchService.activeInstance
        service?.sendNotification(type, title, body)
    }
}
