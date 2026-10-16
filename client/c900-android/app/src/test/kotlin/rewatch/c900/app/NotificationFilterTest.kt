package rewatch.c900.app

import android.app.Notification
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NotificationFilterTest {

    @Test
    fun testOngoingEventFiltered() {
        val flags = Notification.FLAG_ONGOING_EVENT
        assertTrue(NotificationFilter.shouldFilter(flags, "com.whatsapp", "rewatch.c900.app"))
    }

    @Test
    fun testGroupSummaryFiltered() {
        val flags = Notification.FLAG_GROUP_SUMMARY
        assertTrue(NotificationFilter.shouldFilter(flags, "com.whatsapp", "rewatch.c900.app"))
    }

    @Test
    fun testOwnPackageFiltered() {
        val flags = 0
        assertTrue(NotificationFilter.shouldFilter(flags, "rewatch.c900.app", "rewatch.c900.app"))
    }

    @Test
    fun testNullOrBlankPackageFiltered() {
        assertTrue(NotificationFilter.shouldFilter(0, null, "rewatch.c900.app"))
        assertTrue(NotificationFilter.shouldFilter(0, "", "rewatch.c900.app"))
        assertTrue(NotificationFilter.shouldFilter(0, "   ", "rewatch.c900.app"))
    }

    @Test
    fun testNormalNotificationAllowed() {
        val flags = 0
        assertFalse(NotificationFilter.shouldFilter(flags, "com.whatsapp", "rewatch.c900.app"))
    }

    @Test
    fun testDuplicateWithinWindowDropped() {
        var virtualTime = 1000L
        val dedupe = NotificationDeduplicator(windowMs = 2000L, nowMs = { virtualTime })

        // First message: allowed (one send)
        assertFalse(dedupe.shouldDrop("com.whatsapp", "Alice", "Hello"))

        // Same triplet 500 ms later: dropped
        virtualTime = 1500L
        assertTrue(dedupe.shouldDrop("com.whatsapp", "Alice", "Hello"))

        // Same triplet 1999 ms later: dropped
        virtualTime = 2999L
        assertTrue(dedupe.shouldDrop("com.whatsapp", "Alice", "Hello"))

        // Same triplet at 2000 ms later (now 3000L): allowed
        virtualTime = 3000L
        assertFalse(dedupe.shouldDrop("com.whatsapp", "Alice", "Hello"))
    }

    @Test
    fun testDifferentMessageWithinWindowAllowed() {
        var virtualTime = 1000L
        val dedupe = NotificationDeduplicator(windowMs = 2000L, nowMs = { virtualTime })

        assertFalse(dedupe.shouldDrop("com.whatsapp", "Alice", "Hello"))
        virtualTime = 1100L
        // Different body: allowed
        assertFalse(dedupe.shouldDrop("com.whatsapp", "Alice", "World"))
        virtualTime = 1200L
        // Different sender: allowed
        assertFalse(dedupe.shouldDrop("com.whatsapp", "Bob", "World"))
        virtualTime = 1300L
        // Different package: allowed
        assertFalse(dedupe.shouldDrop("org.telegram.messenger", "Bob", "World"))
    }
}
