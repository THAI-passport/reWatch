package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class DisconnectedMessageQueueTest {

    @Test
    fun testRetainsUpToFiveNewestMessages() {
        val q = DisconnectedMessageQueue(maxCapacity = 5)

        for (i in 1..8) {
            q.enqueue(type = 13, title = "Title $i", body = "Body $i")
        }

        assertEquals(5, q.size)
        val drained = q.drain()
        assertEquals(5, drained.size)

        // Oldest (1, 2, 3) must have been dropped; 4, 5, 6, 7, 8 retained
        assertEquals("Title 4", drained[0].title)
        assertEquals("Title 5", drained[1].title)
        assertEquals("Title 6", drained[2].title)
        assertEquals("Title 7", drained[3].title)
        assertEquals("Title 8", drained[4].title)

        assertTrue(q.isEmpty)
    }

    @Test
    fun testDrainEmptiesQueue() {
        val q = DisconnectedMessageQueue()
        q.enqueue(type = 1, title = "A", body = "B")
        q.enqueue(type = 2, title = "C", body = "D")
        assertEquals(2, q.size)

        val items = q.drain()
        assertEquals(2, items.size)
        assertEquals(0, q.size)
        assertTrue(q.isEmpty)
    }
}
