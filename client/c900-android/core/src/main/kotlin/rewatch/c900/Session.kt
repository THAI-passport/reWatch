package rewatch.c900

/**
 * Connection/session state machine (CLIENT-DESIGN 3.4). Pure logic: the platform layer feeds GATT
 * events in and performs the actions it returns. Never bonds; bond triggers become a user prompt.
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
    val inbound = ArrayList<Frames.Inbound.Cmd>()

    fun connecting() { state = State.CONNECTING }

    /** Services discovered: require the command service, refuse denied ones for use. */
    fun discovered(serviceUuids: List<String>, commandChars: List<String>): List<Action> {
        val cmdOk = serviceUuids.any { it.equals(Gatt.COMMAND_SERVICE, true) } &&
            commandChars.count { it.equals(Gatt.COMMAND_WRITE, true) } == 1 &&
            commandChars.count { it.equals(Gatt.COMMAND_NOTIFY, true) } == 1
        if (!cmdOk) { state = State.ERROR; return listOf(Action.Fail("command service missing or ambiguous")) }
        state = State.READING_INFO
        // Connect order (I-35): 0x2A27, 0x2A26, features 0x2A28, battery 0x2A19.
        return listOf("2a27", "2a26", "2a28", "2a19").map { Action.Read("0000$it-0000-1000-8000-00805f9b34fb") }
    }

    fun readResult(uuid: String, value: ByteArray?): List<Action> {
        when (uuid.lowercase().substring(4, 8)) {
            "2a27" -> ver = Frames.verFromHwRevision(value)
            "2a28" -> features = value
            "2a19" -> battery = value?.firstOrNull()?.toInt()?.and(0xFF)
            "2a26" -> {}
        }
        if (uuid.lowercase().startsWith("00002a19")) {
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
        return emptyList()
    }

    /** Feature bit, e.g. bit(15, 0x40) = watch-side pairing support. False when unknown. */
    fun bit(index: Int, mask: Int): Boolean = features?.let { it.size > index && (it[index].toInt() and mask) != 0 } ?: false

    /** Inbound DF frame from the watch. Returns the app-style ACK to send, plus a bond prompt when relevant. */
    fun onCommand(c: Frames.Inbound.Cmd, frameLen: Int): List<Action> {
        inbound.add(c)
        val acts = mutableListOf<Action>(Action.Ack(Frames.ack(c.cmd, c.key, x = 0, status = 1)))
        if ((c.cmd == 0x0C && c.key == 19) || (c.cmd == 0x0E && c.key == 1)) {
            acts.add(Action.AskUserBond("watch asked for classic pairing (cmd 0x%02x key %d)".format(c.cmd, c.key)))
        }
        return acts
    }

    fun disconnected() { state = State.DISCONNECTED }
    fun commands(): Commands = Commands(ver ?: error("not ready"))
}
