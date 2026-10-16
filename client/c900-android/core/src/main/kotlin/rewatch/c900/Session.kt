package rewatch.c900

/**
 * Connection/session state machine (CLIENT-DESIGN 3.4). Pure logic: the platform layer feeds GATT
 * events in and performs the actions it returns. Never bonds; 0x0C key 19 becomes a user prompt, 0x0E key 1 is cached silently (owner decision).
 */
class Session {
    enum class State { IDLE, CONNECTING, DISCOVERING, READING_INFO, READY, DISCONNECTED, ERROR }

    sealed class Action {
        data class Read(val uuid: String) : Action()
        object EnableNotify : Action()
        data class AskUserBond(val reason: String) : Action()
        data class Fail(val reason: String) : Action()
        data class Ack(val bytes: ByteArray) : Action()
    }

    var state = State.IDLE; private set
    var ver: Int? = null; private set
    var features: ByteArray? = null; private set
    var battery: Int? = null; private set
    /** Classic BT address the watch announced (cmd 0x0E key 1); personal data, never log or persist it. */
    var classicMac: ByteArray? = null; private set
    /** Most recent inbound commands, capped so a long session cannot grow without bound (R08 F-04). */
    val inbound = ArrayDeque<Frames.Inbound.Cmd>()
    private val pendingReads = mutableSetOf<String>()

    fun connecting() { state = State.CONNECTING }

    /** Services discovered: require the command service, refuse denied ones for use. */
    fun discovered(serviceUuids: List<String>, commandChars: List<String>): List<Action> {
        val cmdOk = serviceUuids.any { it.equals(Gatt.COMMAND_SERVICE, true) } &&
            commandChars.count { it.equals(Gatt.COMMAND_WRITE, true) } == 1 &&
            commandChars.count { it.equals(Gatt.COMMAND_NOTIFY, true) } == 1
        if (!cmdOk) { state = State.ERROR; return listOf(Action.Fail("command service missing or ambiguous")) }
        state = State.READING_INFO
        // Connect order (I-35): 0x2A27, 0x2A26, features 0x2A28, battery 0x2A19.
        val reads = listOf("2a27", "2a26", "2a28", "2a19")
        pendingReads.clear(); pendingReads.addAll(reads)
        return reads.map { Action.Read("0000$it-0000-1000-8000-00805f9b34fb") }
    }

    /**
     * One info read finished (value null = read failed). Reads may complete in any order; the version
     * check runs once all four have reported (R08 F-01). Accepts 16-bit ("2a27") or 128-bit UUIDs (F-03).
     */
    fun readResult(uuid: String, value: ByteArray?): List<Action> {
        val short = shortUuid(uuid) ?: return emptyList()
        if (!pendingReads.remove(short)) return emptyList()
        when (short) {
            "2a27" -> ver = Frames.verFromHwRevision(value)
            "2a28" -> features = value
            "2a19" -> battery = value?.firstOrNull()?.toInt()?.and(0xFF)
        }
        if (pendingReads.isNotEmpty()) return emptyList()
        val v = ver
        if (v == null || v !in Commands.REVIEWED_VERS) {
            state = State.ERROR
            return listOf(Action.Fail("ver ${v?.let { "0x%02x".format(it) }} not reviewed"))
        }
        if (features?.firstOrNull()?.toInt()?.and(0xFF) != 0xAA) {
            // Unknown features: stay usable but every feature-gated command is off (I-32).
            features = null
        }
        state = State.READY
        return listOf(Action.EnableNotify)
    }

    private fun shortUuid(uuid: String): String? {
        val u = uuid.lowercase()
        return when {
            u.length == 4 -> u
            u.length == 36 && u.startsWith("0000") && u.endsWith("-0000-1000-8000-00805f9b34fb") -> u.substring(4, 8)
            else -> null
        }
    }

    /** Feature bit, e.g. bit(15, 0x40) = watch-side pairing support. False when unknown. */
    fun bit(index: Int, mask: Int): Boolean = features?.let { it.size > index && (it[index].toInt() and mask) != 0 } ?: false

    /** Inbound DF frame from the watch. Returns the app-style ACK to send, plus a bond prompt when relevant. */
    fun onCommand(c: Frames.Inbound.Cmd, frameLen: Int): List<Action> {
        inbound.addLast(c)
        while (inbound.size > INBOUND_KEEP) inbound.removeFirst()
        val acts = mutableListOf<Action>(Action.Ack(Frames.ack(c.cmd, c.key, x = 0, status = 1)))
        if (c.cmd == 0x0C && c.key == 19) {
            acts.add(Action.AskUserBond("watch asked for classic pairing (cmd 0x0c key 19)"))
        } else if (c.cmd == 0x0E && c.key == 1 && c.payload.size >= 6) {
            // Owner decision 2026-10-14 (CLIENT-DESIGN 3.4): the watch sends this after message pushes and
            // syncs; cache the classic MAC, ack, never prompt and never bond. Kept in memory only.
            classicMac = c.payload.copyOfRange(0, 6)
        }
        return acts
    }

    fun disconnected() { state = State.DISCONNECTED; pendingReads.clear() }
    fun commands(): Commands = Commands(ver ?: error("not ready"))

    companion object {
        const val INBOUND_KEEP = 256
    }
}
