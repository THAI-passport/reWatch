package rewatch.c900.app

/**
 * Message buffer used when watch is disconnected.
 * Retains up to [maxCapacity] newest messages; drops oldest when full.
 */
class DisconnectedMessageQueue(val maxCapacity: Int = MAX_CAPACITY) {
    data class QueuedMessage(val type: Int, val title: String, val body: String)

    private val queue = ArrayDeque<QueuedMessage>()

    @Synchronized
    fun enqueue(type: Int, title: String, body: String) {
        if (queue.size >= maxCapacity) {
            queue.removeFirst()
        }
        queue.addLast(QueuedMessage(type, title, body))
    }

    @Synchronized
    fun drain(): List<QueuedMessage> {
        val items = queue.toList()
        queue.clear()
        return items
    }

    @Synchronized
    fun clear() {
        queue.clear()
    }

    val size: Int
        @Synchronized get() = queue.size

    val isEmpty: Boolean
        @Synchronized get() = queue.isEmpty()

    companion object {
        const val MAX_CAPACITY = 5
    }
}
