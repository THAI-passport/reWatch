package rewatch.c900.app

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

/**
 * NotificationListenerService capturing posted notifications and forwarding them
 * to [WatchService] as cmd 0x02 key 18 message frames.
 *
 * Package mapping uses the new type table (C900-Q04 section 5, other = 13).
 * If disconnected, retains the newest 5 messages.
 * Privacy: notification text, MAC addresses, and device names are never logged.
 */
class NotifyListener : NotificationListenerService() {

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        val n = sbn?.notification ?: return
        val pkg = sbn.packageName ?: return

        val type = NotificationMapper.mapPackage(pkg)
        if (type == NotificationMapper.TYPE_IGNORE) return

        val extras = n.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val body = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""

        if (title.isBlank() && body.isBlank()) return

        val service = WatchService.activeInstance
        service?.sendNotification(type, title, body)
    }
}
