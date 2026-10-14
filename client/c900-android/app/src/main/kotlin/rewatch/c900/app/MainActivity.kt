package rewatch.c900.app

import android.Manifest
import android.app.Activity
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.ProgressBar
import android.widget.TextView

/**
 * Device picker activity scanning for C900 companion watches (advertised name "Watch Ultra").
 *
 * Scans using BLUETOOTH_SCAN (neverForLocation) without location permissions (R10).
 * Lists discovered matching devices and connects via [WatchService.connectDevice] on tap.
 * Privacy: zero logging of device MAC addresses or raw names.
 */
class MainActivity : Activity() {

    private val handler = Handler(Looper.getMainLooper())
    private var isScanning = false
    private val discoveredDevices = mutableListOf<BluetoothDevice>()
    private lateinit var listAdapter: ArrayAdapter<String>
    private lateinit var scanButton: Button
    private lateinit var statusText: TextView
    private lateinit var progressBar: ProgressBar

    private var watchService: WatchService? = null
    private var pendingConnectDevice: BluetoothDevice? = null

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as? WatchService.LocalBinder
            watchService = binder?.getService()
            pendingConnectDevice?.let { dev ->
                watchService?.connectDevice(dev)
                pendingConnectDevice = null
            }
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            watchService = null
        }
    }

    private var totalPacketsSeen = 0

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult?) {
            totalPacketsSeen++
            val device = result?.device ?: return
            val record = result.scanRecord
            val name = record?.deviceName ?: try {
                device.name
            } catch (_: SecurityException) {
                null
            }
            val mfgData = record?.getManufacturerSpecificData(COMPANY_ID_C900)
                ?: record?.getManufacturerSpecificData(0x4C31)

            if (isMatchingDevice(name, mfgData, device.address)) {
                addDiscoveredDevice(device)
            } else {
                handler.post {
                    if (discoveredDevices.isEmpty() && isScanning) {
                        statusText.text = "Scanning for $TARGET_DEVICE_NAME... (seen $totalPacketsSeen)"
                    }
                }
            }
        }

        override fun onScanFailed(errorCode: Int) {
            handler.post {
                stopScan()
                statusText.text = "Scan failed: code $errorCode"
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = createViewHierarchy()
        setContentView(root)
        checkPermissionsOnLaunch()
        bindWatchService()
    }

    override fun onDestroy() {
        stopScan()
        try {
            unbindService(serviceConnection)
        } catch (_: IllegalArgumentException) {
        }
        super.onDestroy()
    }

    private fun createViewHierarchy(): View {
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 48, 32, 32)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        val title = TextView(this).apply {
            text = "reWatch — Device Picker"
            textSize = 20f
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 16)
        }
        layout.addView(title)

        val navBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 16)
        }
        val statusNavButton = Button(this).apply {
            text = "Status Screen"
            setOnClickListener {
                startActivity(Intent(this@MainActivity, StatusActivity::class.java))
            }
        }
        val settingsNavButton = Button(this).apply {
            text = "Settings"
            setOnClickListener {
                startActivity(Intent(this@MainActivity, SettingsActivity::class.java))
            }
        }
        navBar.addView(statusNavButton)
        navBar.addView(settingsNavButton)
        layout.addView(navBar)

        statusText = TextView(this).apply {
            text = "Target: $TARGET_DEVICE_NAME"
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 16)
        }
        layout.addView(statusText)

        progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            isIndeterminate = true
            visibility = View.INVISIBLE
        }
        layout.addView(progressBar)

        scanButton = Button(this).apply {
            text = "Start Scan"
            setOnClickListener {
                if (isScanning) stopScan() else checkPermissionsAndStartScan()
            }
        }
        layout.addView(scanButton)

        listAdapter = ArrayAdapter(this, android.R.layout.simple_list_item_1, mutableListOf<String>())
        val listView = ListView(this).apply {
            adapter = listAdapter
            setOnItemClickListener { _, _, position, _ ->
                if (position in discoveredDevices.indices) {
                    val device = discoveredDevices[position]
                    onDeviceSelected(device)
                }
            }
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        }
        layout.addView(listView)

        return layout
    }

    private fun bindWatchService() {
        val intent = Intent(this, WatchService::class.java)
        bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
    }

    private fun checkPermissionsOnLaunch() {
        val needed = requiredPermissions(this)
        if (needed.isNotEmpty()) {
            requestPermissions(needed.toTypedArray(), REQUEST_CODE_PERMISSIONS_ON_LAUNCH)
        }
    }

    private fun checkPermissionsAndStartScan() {
        val needed = requiredPermissions(this)
        if (needed.isNotEmpty()) {
            requestPermissions(needed.toTypedArray(), REQUEST_CODE_PERMISSIONS_SCAN)
            return
        }
        startScan()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        val allGranted = grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }
        if (requestCode == REQUEST_CODE_PERMISSIONS_SCAN) {
            if (allGranted) {
                startScan()
            } else {
                statusText.text = "Bluetooth scan permissions required"
            }
        } else if (requestCode == REQUEST_CODE_PERMISSIONS_ON_LAUNCH) {
            if (!allGranted) {
                statusText.text = "Permissions required to scan and connect"
            }
        }
    }

    private fun startScan() {
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        val adapter = bluetoothManager?.adapter
        if (adapter == null || !adapter.isEnabled) {
            statusText.text = "Bluetooth is disabled"
            return
        }

        val scanner = adapter.bluetoothLeScanner
        if (scanner == null) {
            statusText.text = "BLE scanner unavailable"
            return
        }

        discoveredDevices.clear()
        listAdapter.clear()
        totalPacketsSeen = 0
        isScanning = true
        scanButton.text = "Stop Scan"
        progressBar.visibility = View.VISIBLE
        statusText.text = "Scanning for $TARGET_DEVICE_NAME..."

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        try {
            // First attempt: unfiltered scan to bypass controller-side parameter rejections
            scanner.startScan(null, settings, scanCallback)
            handler.postDelayed({ stopScan() }, SCAN_TIMEOUT_MS)
        } catch (_: Exception) {
            try {
                scanner.startScan(listOf(ScanFilter.Builder().build()), settings, scanCallback)
                handler.postDelayed({ stopScan() }, SCAN_TIMEOUT_MS)
            } catch (_: SecurityException) {
                statusText.text = "SecurityException during BLE scan"
                stopScan()
            }
        }
    }

    private fun stopScan() {
        if (!isScanning) return
        isScanning = false
        scanButton.text = "Start Scan"
        progressBar.visibility = View.INVISIBLE
        val count = discoveredDevices.size
        statusText.text = if (count > 0) "Found $count device(s)" else "Scan finished (seen $totalPacketsSeen pkts, 0 matched)"

        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        val scanner = bluetoothManager?.adapter?.bluetoothLeScanner
        try {
            scanner?.stopScan(scanCallback)
        } catch (_: SecurityException) {
        }
    }

    private fun addDiscoveredDevice(device: BluetoothDevice) {
        handler.post {
            if (discoveredDevices.none { it.address == device.address }) {
                discoveredDevices.add(device)
                val displayLabel = "$TARGET_DEVICE_NAME #${discoveredDevices.size}"
                listAdapter.add(displayLabel)
                statusText.text = "Found ${discoveredDevices.size} device(s)"
            }
        }
    }

    private fun onDeviceSelected(device: BluetoothDevice) {
        stopScan()
        statusText.text = "Connecting to device..."

        val serviceIntent = Intent(this, WatchService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }

        val active = WatchService.activeInstance ?: watchService
        if (active != null) {
            active.connectDevice(device)
        } else {
            pendingConnectDevice = device
        }

        // Open status screen to observe connection progress
        startActivity(Intent(this, StatusActivity::class.java))
    }

    companion object {
        const val TARGET_DEVICE_NAME = "Watch Ultra" // FACTS section 1 [C]
        const val TARGET_DEVICE_MAC_SUFFIX = "D7:CC" // [H] FACTS section 1.1, LIVE-SESSION-1
        const val SCAN_TIMEOUT_MS = 15_000L
        const val REQUEST_CODE_PERMISSIONS_ON_LAUNCH = 2001
        const val REQUEST_CODE_PERMISSIONS_SCAN = 2002

        const val COMPANY_ID_C900 = 0x314C // [H] FACTS section 1.1

        fun isMatchingDevice(
            deviceName: String?,
            manufacturerData: ByteArray? = null,
            deviceAddress: String? = null
        ): Boolean {
            if (deviceName != null) {
                val trimmed = deviceName.trim()
                if (trimmed.equals(TARGET_DEVICE_NAME, ignoreCase = true) ||
                    trimmed.contains("Watch Ultra", ignoreCase = true) ||
                    trimmed.equals("Watch", ignoreCase = true)
                ) {
                    return true
                }
            }
            if (manufacturerData != null && manufacturerData.size >= 8) {
                val hasMarker = manufacturerData[manufacturerData.size - 2] == 0x12.toByte() &&
                    manufacturerData[manufacturerData.size - 1] == 0x34.toByte()
                if (hasMarker) return true
            }
            if (deviceAddress != null && deviceAddress.endsWith(TARGET_DEVICE_MAC_SUFFIX, ignoreCase = true)) {
                return true
            }
            return false
        }

        fun requiredPermissions(context: Context): List<String> {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return emptyList()
            val needed = mutableListOf<String>()
            if (context.checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                needed.add(Manifest.permission.BLUETOOTH_SCAN)
            }
            if (context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                needed.add(Manifest.permission.BLUETOOTH_CONNECT)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                if (context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                    needed.add(Manifest.permission.POST_NOTIFICATIONS)
                }
            }
            return needed
        }
    }
}
