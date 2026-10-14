package rewatch.c900.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.bluetooth.BluetoothDevice
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Binder
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import rewatch.c900.CommandQueue
import rewatch.c900.Frames
import rewatch.c900.HealthSync
import rewatch.c900.Session

/**
 * Controller for reconnect state and scheduling.
 * A terminal failure (e.g. unsupported watch) stops all reconnection attempts until
 * [connectDevice] is explicitly invoked again.
 */
class ReconnectController(
    private val postDelayed: (Long, Runnable) -> Unit,
    private val removeCallbacks: (Runnable) -> Unit
) {
    var isFailedTerminal = false
        private set
    var isReconnectScheduled = false
        private set
    var hasTargetDevice = false
        private set

    private val reconnectRunnable = Runnable {
        isReconnectScheduled = false
        onReconnect()
    }

    var onReconnect: () -> Unit = {}

    fun onTerminalFail() {
        isFailedTerminal = true
        cancelReconnect()
    }

    fun onDeviceConnecting(hasDevice: Boolean) {
        hasTargetDevice = hasDevice
        isFailedTerminal = false
        cancelReconnect()
    }

    fun scheduleReconnect(delayMs: Long) {
        if (isFailedTerminal || !hasTargetDevice) return
        cancelReconnect()
        isReconnectScheduled = true
        postDelayed(delayMs, reconnectRunnable)
    }

    fun cancelReconnect() {
        isReconnectScheduled = false
        removeCallbacks(reconnectRunnable)
    }
}

/**
 * Foreground service (connectedDevice) managing C900 BLE connection, Session state machine,
 * CommandQueue, and HealthSync (PROTOCOL 11, CLIENT-DESIGN 3).
 *
 * Reconnect rules (PROTOCOL 11): 10000 ms on disconnect, 3000 ms on connect failure.
 * Inbound 0x0E key 1: cached silently in memory, ACK sent, never prompts (owner decision).
 * Inbound 0x0C key 19: user notification prompt shown; default is no. Never calls createBond.
 * Privacy: no notification text, MAC addresses or device names are ever logged.
 */
class WatchService : Service() {

    inner class LocalBinder : Binder() {
        fun getService(): WatchService = this@WatchService
    }

    private val binder = LocalBinder()
    private val handler = Handler(Looper.getMainLooper())

    lateinit var session: Session private set
    lateinit var healthSync: HealthSync private set
    lateinit var commandQueue: CommandQueue private set
    lateinit var gattLink: GattLink private set

    val disconnectedQueue = DisconnectedMessageQueue()
    private var targetDevice: BluetoothDevice? = null
    private var isDestroyed = false

    val reconnectController = ReconnectController(
        postDelayed = { delayMs, r -> handler.postDelayed(r, delayMs) },
        removeCallbacks = { r -> handler.removeCallbacks(r) }
    ).apply {
        onReconnect = {
            if (!isDestroyed) {
                targetDevice?.let { dev ->
                    session.connecting()
                    gattLink.connect(dev)
                }
            }
        }
    }

    val isFailedTerminal get() = reconnectController.isFailedTerminal

    private val tickRunnable = object : Runnable {
        override fun run() {
            if (isDestroyed) return
            commandQueue.tick()
            healthSync.tick()
            handler.postDelayed(this, 1000L)
        }
    }

    private val gattListener = object : GattLink.Listener {
        override fun onConnected() {
            session.connecting()
        }

        override fun onDisconnected(status: Int, newState: Int) {
            val wasConnecting = session.state == Session.State.CONNECTING
            session.disconnected()
            commandQueue.abortAll("disconnected")

            if (reconnectController.isFailedTerminal) return

            // Reconnect timing (PROTOCOL 11): 3000 ms if connect failed, 10000 ms on disconnect
            val delayMs = if (status != 0 || wasConnecting) RECONNECT_CONNECT_FAIL_MS else RECONNECT_DISCONNECT_MS
            scheduleReconnect(delayMs)
        }

        override fun onServicesDiscovered(serviceUuids: List<String>, commandChars: List<String>) {
            val actions = session.discovered(serviceUuids, commandChars)
            actions.forEach { gattLink.dispatchAction(it) }
        }

        override fun onCharacteristicReadResult(uuid: String, value: ByteArray?) {
            val actions = session.readResult(uuid, value)
            actions.forEach { gattLink.dispatchAction(it) }
            if (session.state == Session.State.READY) {
                flushDisconnectedQueue()
            }
        }

        override fun onAckReceived(ack: Frames.Inbound.Ack) {
            commandQueue.onAck(ack)
        }

        override fun onCommandReceived(cmd: Frames.Inbound.Cmd, frameLen: Int) {
            healthSync.onCommand(cmd)
            val actions = session.onCommand(cmd, frameLen)
            actions.forEach { gattLink.dispatchAction(it) }
        }

        override fun onAskUserBond(reason: String) {
            // Inbound 0x0C key 19: show user notification prompt asking permission; default is No.
            showBondPromptNotification()
        }

        override fun onError(reason: String) {
            gattLink.disconnect()
            session.disconnected()
            commandQueue.abortAll(reason)
            scheduleReconnect(RECONNECT_CONNECT_FAIL_MS)
        }

        override fun onTerminalFail(reason: String) {
            reconnectController.onTerminalFail()
            session.disconnected()
            commandQueue.abortAll("terminal failure: $reason")
            showTerminalFailNotification(reason)
        }
    }

    override fun onCreate() {
        super.onCreate()
        activeInstance = this

        session = Session()
        healthSync = HealthSync(nowMs = { SystemClock.elapsedRealtime() })
        gattLink = GattLink(this, handler, gattListener)
        commandQueue = CommandQueue(
            write = { piece -> gattLink.writePiece(piece) },
            nowMs = { SystemClock.elapsedRealtime() }
        )

        createNotificationChannels()
        startServiceForeground()
        handler.post(tickRunnable)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onDestroy() {
        isDestroyed = true
        if (activeInstance === this) {
            activeInstance = null
        }
        reconnectController.cancelReconnect()
        handler.removeCallbacksAndMessages(null)
        gattLink.disconnect()
        super.onDestroy()
    }
    fun connectDevice(device: BluetoothDevice) {
        handler.post {
            targetDevice = device
            reconnectController.onDeviceConnecting(true)
            session.connecting()
            gattLink.connect(device)
        }
    }

    fun sendNotification(type: Int, title: String, body: String) {
        handler.post {
            if (session.state == Session.State.READY) {
                try {
                    val cmd = session.commands().message(type, title, body)
                    commandQueue.submit(cmd) { /* completed */ }
                } catch (_: IllegalStateException) {
                    disconnectedQueue.enqueue(type, title, body)
                }
            } else {
                disconnectedQueue.enqueue(type, title, body)
            }
        }
    }

    private fun flushDisconnectedQueue() {
        val pending = disconnectedQueue.drain()
        for (msg in pending) {
            sendNotification(msg.type, msg.title, msg.body)
        }
    }

    private fun scheduleReconnect(delayMs: Long) {
        if (!isDestroyed) {
            reconnectController.scheduleReconnect(delayMs)
        }
    }

    private fun createNotificationChannels() {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return
        val serviceChannel = NotificationChannel(
            CHANNEL_SERVICE,
            "reWatch Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Maintains connection to C900 companion watch"
        }
        val promptChannel = NotificationChannel(
            CHANNEL_PROMPT,
            "reWatch Prompts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Requests confirmation for pairing and security actions"
        }
        nm.createNotificationChannel(serviceChannel)
        nm.createNotificationChannel(promptChannel)
    }

    private fun startServiceForeground() {
        val notification = Notification.Builder(this, CHANNEL_SERVICE)
            .setContentTitle("reWatch")
            .setContentText("C900 companion service running")
            .setOngoing(true)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID_SERVICE,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE
            )
        } else {
            startForeground(NOTIFICATION_ID_SERVICE, notification)
        }
    }

    private fun showBondPromptNotification() {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return
        val prompt = Notification.Builder(this, CHANNEL_PROMPT)
            .setContentTitle("Pairing Request")
            .setContentText("The watch requested classic pairing (cmd 0x0c key 19). Pairing is denied by default.")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setAutoCancel(true)
            .build()
        nm.notify(NOTIFICATION_ID_PROMPT, prompt)
    }

    private fun showTerminalFailNotification(reason: String) {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return
        val prompt = Notification.Builder(this, CHANNEL_PROMPT)
            .setContentTitle("Watch not supported")
            .setContentText("The connected watch is not supported: $reason")
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setAutoCancel(true)
            .build()
        nm.notify(NOTIFICATION_ID_TERMINAL, prompt)
    }

    companion object {
        const val RECONNECT_DISCONNECT_MS = 10_000L     // PROTOCOL 11
        const val RECONNECT_CONNECT_FAIL_MS = 3_000L    // PROTOCOL 11

        const val CHANNEL_SERVICE = "rewatch_service"
        const val CHANNEL_PROMPT = "rewatch_prompt"

        const val NOTIFICATION_ID_SERVICE = 1001
        const val NOTIFICATION_ID_PROMPT = 1002
        const val NOTIFICATION_ID_TERMINAL = 1003

        var activeInstance: WatchService? = null
            private set
    }
}
