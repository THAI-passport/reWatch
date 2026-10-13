package rewatch.c900

/** GATT constants (PROTOCOL section 2, FACTS 1.1). The transport may only use COMMAND_* and the read-only DI/battery chars. */
object Gatt {
    const val COMMAND_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9f"
    const val COMMAND_WRITE = "6e400002-b5a3-f393-e0a9-e50e24dcca9f"
    const val COMMAND_NOTIFY = "6e400003-b5a3-f393-e0a9-e50e24dcca9f"
    const val PIECE = 20
    const val PIECE_GAP_MS = 20L

    private val DENY_SHORT = setOf("ff00", "ff01", "ff02", "ff03", "18a8", "2aa8", "2aa9", "5610",
        "ff10", "fff1", "ff12", "ff13", "ff14")

    /** OTA/DFU and unknown vendor services: never subscribe, read or write (I-14, I-54, S-21). */
    fun isDenied(uuid: String): Boolean {
        val u = uuid.trim().lowercase()
        if (u.endsWith("dcca9e") || "5610" in u) return true
        val short = when {
            u.length == 36 && u.startsWith("0000") && u.endsWith("-0000-1000-8000-00805f9b34fb") -> u.substring(4, 8)
            u.length == 4 -> u
            else -> ""
        }
        return short in DENY_SHORT
    }

    /** 20-byte ATT pieces as the app writes them (I-16). */
    fun pieces(frame: ByteArray): List<ByteArray> = frame.toList().chunked(PIECE).map { it.toByteArray() }

    /** QR text -> BLE MAC, the app's two rules (S-22 [C]); null if not a 17-char MAC. */
    fun macFromQr(text: String?): String? {
        val t = text ?: return null
        val mac = when {
            t.startsWith("LE") && t.length > 20 -> t.substring(3, 20)
            "?para=" in t -> t.substring(t.indexOf("?para=") + 6)
            else -> return null
        }
        return if (Regex("^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$").matches(mac)) mac.uppercase() else null
    }
}
