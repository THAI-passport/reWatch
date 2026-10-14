package rewatch.c900.app

import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothProfile
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import rewatch.c900.FrameReader
import rewatch.c900.Frames
import rewatch.c900.Gatt
import rewatch.c900.Session
import java.util.UUID

/**
 * Android BluetoothGatt adapter turning [Session.Action] into serialised GATT operations.
 * Enforces strictly ONE GATT operation in flight at a time, spaces ATT pieces [Gatt.PIECE_GAP_MS] apart,
 * and never touches denied UUIDs (I-14, I-54). Never calls createBond (I-30).
 *
 * Threading model: posts every [BluetoothGattCallback] event to [handler] so that [Session],
 * [rewatch.c900.CommandQueue], and [rewatch.c900.HealthSync] are touched strictly on the main looper thread.
 */
class GattLink(
    private val context: Context? = null,
    private val handler: Handler = Handler(Looper.getMainLooper()),
    private val listener: Listener,
    private val post: (Runnable) -> Unit = { handler.post(it) }
) {
    interface Listener {
        fun onConnected()
        fun onDisconnected(status: Int, newState: Int)
        fun onServicesDiscovered(serviceUuids: List<String>, commandChars: List<String>)
        fun onCharacteristicReadResult(uuid: String, value: ByteArray?)
        fun onAckReceived(ack: Frames.Inbound.Ack)
        fun onCommandReceived(cmd: Frames.Inbound.Cmd, frameLen: Int)
        fun onAskUserBond(reason: String)
        fun onError(reason: String)
        fun onTerminalFail(reason: String)
    }

    internal var bluetoothGatt: BluetoothGatt? = null
    private var activeOp: GattOp? = null
    private var frameReader = FrameReader()

    val pacingScheduler = PacingScheduler(
        execute = { op -> executeOp(op) },
        postDelayed = { delayMs, task -> handler.postDelayed(task, delayMs) }
    )

    fun isCurrent(gatt: BluetoothGatt?): Boolean = gatt != null && gatt === bluetoothGatt

    internal val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            post {
                if (gatt !== bluetoothGatt) {
                    try {
                        gatt.close()
                    } catch (_: SecurityException) {
                    }
                    return@post
                }
                if (status != BluetoothGatt.GATT_SUCCESS || newState == BluetoothProfile.STATE_DISCONNECTED) {
                    pacingScheduler.clear()
                    activeOp = null
                    frameReader = FrameReader()
                    try {
                        gatt.disconnect()
                        gatt.close()
                    } catch (_: SecurityException) {
                    }
                    if (bluetoothGatt === gatt) {
                        bluetoothGatt = null
                    }
                    listener.onDisconnected(status, newState)
                } else if (newState == BluetoothProfile.STATE_CONNECTED) {
                    listener.onConnected()
                    try {
                        gatt.discoverServices()
                    } catch (_: SecurityException) {
                        listener.onError("discoverServices security exception")
                    }
                }
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            post {
                if (gatt !== bluetoothGatt) return@post
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    listener.onError("discoverServices failed: status $status")
                    return@post
                }
                val serviceUuids = gatt.services.map { it.uuid.toString() }
                val cmdService = gatt.services.firstOrNull { it.uuid.toString().equals(Gatt.COMMAND_SERVICE, ignoreCase = true) }
                val commandChars = cmdService?.characteristics?.map { it.uuid.toString() } ?: emptyList()
                listener.onServicesDiscovered(serviceUuids, commandChars)
            }
        }

        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
            status: Int
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                handleReadResult(characteristic.uuid.toString(), if (status == BluetoothGatt.GATT_SUCCESS) value else null)
            }
        }

        @Suppress("DEPRECATION")
        @Deprecated("Deprecated in Java")
        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                handleReadResult(characteristic.uuid.toString(), if (status == BluetoothGatt.GATT_SUCCESS) characteristic.value else null)
            }
        }

        override fun onCharacteristicWrite(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                val op = activeOp
                if (op is GattOp.WritePiece) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                }
            }
        }

        override fun onDescriptorWrite(
            gatt: BluetoothGatt,
            descriptor: BluetoothGattDescriptor,
            status: Int
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                val op = activeOp
                if (op is GattOp.EnableNotify) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                }
            }
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                handleNotificationBytes(characteristic.uuid.toString(), value)
            }
        }

        @Suppress("DEPRECATION")
        @Deprecated("Deprecated in Java")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            post {
                if (gatt !== bluetoothGatt) return@post
                handleNotificationBytes(characteristic.uuid.toString(), characteristic.value ?: ByteArray(0))
            }
        }
    }

    private fun handleReadResult(uuid: String, value: ByteArray?) {
        val op = activeOp
        if (op is GattOp.Read) {
            activeOp = null
            pacingScheduler.onComplete(op)
        }
        listener.onCharacteristicReadResult(uuid, value)
    }

    private fun handleNotificationBytes(charUuid: String, bytes: ByteArray) {
        if (!charUuid.equals(Gatt.COMMAND_NOTIFY, ignoreCase = true)) return
        val frames = frameReader.feed(bytes)
        for (f in frames) {
            when (f) {
                is Frames.Inbound.Ack -> listener.onAckReceived(f)
                is Frames.Inbound.Cmd -> listener.onCommandReceived(f, f.payload.size + 9)
                is Frames.Inbound.Bad -> {
                    // Frame invalid or bad header/length/checksum
                }
            }
        }
    }

    fun connect(device: BluetoothDevice) {
        disconnect()
        bluetoothGatt = device.connectGatt(context, false, gattCallback)
    }

    fun disconnect() {
        pacingScheduler.clear()
        activeOp = null
        frameReader = FrameReader()
        try {
            bluetoothGatt?.disconnect()
            bluetoothGatt?.close()
        } catch (_: SecurityException) {
        }
        bluetoothGatt = null
    }

    /** Dispatch a [Session.Action] resulting from state machine transitions. */
    fun dispatchAction(action: Session.Action) {
        when (action) {
            is Session.Action.Read -> {
                if (!Gatt.isDenied(action.uuid)) {
                    pacingScheduler.enqueue(GattOp.Read(action.uuid))
                }
            }
            is Session.Action.EnableNotify -> {
                pacingScheduler.enqueue(GattOp.EnableNotify)
            }
            is Session.Action.Ack -> {
                Gatt.pieces(action.bytes).forEach { piece ->
                    pacingScheduler.enqueue(GattOp.WritePiece(piece))
                }
            }
            is Session.Action.AskUserBond -> {
                listener.onAskUserBond(action.reason)
            }
            is Session.Action.Fail -> {
                disconnect()
                listener.onTerminalFail(action.reason)
            }
        }
    }

    /** Write one ATT piece from [CommandQueue]. */
    fun writePiece(piece: ByteArray) {
        pacingScheduler.enqueue(GattOp.WritePiece(piece))
    }

    private fun executeOp(op: GattOp) {
        val gatt = bluetoothGatt ?: run {
            pacingScheduler.onComplete(op)
            return
        }

        activeOp = op
        when (op) {
            is GattOp.Read -> {
                if (Gatt.isDenied(op.uuid)) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    return
                }
                val char = findCharacteristic(gatt, op.uuid)
                if (char == null) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    listener.onCharacteristicReadResult(op.uuid, null)
                    return
                }
                val initiated = try {
                    gatt.readCharacteristic(char)
                } catch (_: SecurityException) {
                    false
                }
                if (!initiated) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    listener.onCharacteristicReadResult(op.uuid, null)
                }
            }
            is GattOp.WritePiece -> {
                val char = findCommandWriteChar(gatt)
                if (char == null) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    return
                }
                val initiated = try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        gatt.writeCharacteristic(char, op.piece, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE) == 0
                    } else {
                        @Suppress("DEPRECATION")
                        char.value = op.piece
                        char.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                        @Suppress("DEPRECATION")
                        gatt.writeCharacteristic(char)
                    }
                } catch (_: SecurityException) {
                    false
                }
                if (!initiated) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                }
            }
            is GattOp.EnableNotify -> {
                val char = findCommandNotifyChar(gatt)
                if (char == null) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    return
                }
                val cccd = char.getDescriptor(UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"))
                if (cccd == null) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                    return
                }
                val initiated = try {
                    gatt.setCharacteristicNotification(char, true)
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        gatt.writeDescriptor(cccd, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == 0
                    } else {
                        @Suppress("DEPRECATION")
                        cccd.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                        @Suppress("DEPRECATION")
                        gatt.writeDescriptor(cccd)
                    }
                } catch (_: SecurityException) {
                    false
                }
                if (!initiated) {
                    activeOp = null
                    pacingScheduler.onComplete(op)
                }
            }
        }
    }

    private fun findCharacteristic(gatt: BluetoothGatt, uuidStr: String): BluetoothGattCharacteristic? {
        val target = try { UUID.fromString(uuidStr) } catch (_: IllegalArgumentException) { return null }
        for (svc in gatt.services) {
            if (Gatt.isDenied(svc.uuid.toString())) continue
            for (ch in svc.characteristics) {
                if (Gatt.isDenied(ch.uuid.toString())) continue
                if (ch.uuid == target) return ch
            }
        }
        return null
    }

    private fun findCommandWriteChar(gatt: BluetoothGatt): BluetoothGattCharacteristic? {
        val svc = gatt.services.firstOrNull { it.uuid.toString().equals(Gatt.COMMAND_SERVICE, ignoreCase = true) }
        return svc?.characteristics?.firstOrNull { it.uuid.toString().equals(Gatt.COMMAND_WRITE, ignoreCase = true) }
    }

    private fun findCommandNotifyChar(gatt: BluetoothGatt): BluetoothGattCharacteristic? {
        val svc = gatt.services.firstOrNull { it.uuid.toString().equals(Gatt.COMMAND_SERVICE, ignoreCase = true) }
        return svc?.characteristics?.firstOrNull { it.uuid.toString().equals(Gatt.COMMAND_NOTIFY, ignoreCase = true) }
    }
}
