package rewatch.c900.app

import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothProfile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import rewatch.c900.Frames
import java.util.UUID

class GattLinkTest {

    private fun createFakeGatt(): BluetoothGatt {
        val ctor = BluetoothGatt::class.java.getDeclaredConstructor()
        ctor.isAccessible = true
        return ctor.newInstance()
    }

    private class RecordingListener : GattLink.Listener {
        var disconnectedCount = 0
        var connectedCount = 0
        var readResultCount = 0
        var servicesDiscoveredCount = 0
        var commandCount = 0

        override fun onConnected() { connectedCount++ }
        override fun onDisconnected(status: Int, newState: Int) { disconnectedCount++ }
        override fun onServicesDiscovered(serviceUuids: List<String>, commandChars: List<String>) { servicesDiscoveredCount++ }
        override fun onCharacteristicReadResult(uuid: String, value: ByteArray?) { readResultCount++ }
        override fun onAckReceived(ack: Frames.Inbound.Ack) {}
        override fun onCommandReceived(cmd: Frames.Inbound.Cmd, frameLen: Int) { commandCount++ }
        override fun onAskUserBond(reason: String) {}
        override fun onError(reason: String) {}
        override fun onTerminalFail(reason: String) {}
    }

    @Test
    fun testIsCurrentIdentifiesActiveConnection() {
        val listener = RecordingListener()
        val gattLink = GattLink(
            listener = listener,
            post = { it.run() }
        )

        val gatt1 = createFakeGatt()
        val gatt2 = createFakeGatt()

        assertFalse(gattLink.isCurrent(null))
        assertFalse(gattLink.isCurrent(gatt1))

        gattLink.bluetoothGatt = gatt1
        assertTrue(gattLink.isCurrent(gatt1))
        assertFalse(gattLink.isCurrent(gatt2))

        gattLink.bluetoothGatt = gatt2
        assertFalse(gattLink.isCurrent(gatt1))
        assertTrue(gattLink.isCurrent(gatt2))
    }

    @Test
    fun testStaleDisconnectAfterReconnectDoesNotCallListenerOnDisconnected() {
        val listener = RecordingListener()
        val gattLink = GattLink(
            listener = listener,
            post = { it.run() }
        )

        val oldGatt = createFakeGatt()
        val newGatt = createFakeGatt()

        // 1. Initial connection
        gattLink.bluetoothGatt = oldGatt

        // 2. Service reconnects, making newGatt the active connection
        gattLink.bluetoothGatt = newGatt

        // 3. Stale disconnect callback from oldGatt runs on the looper
        gattLink.gattCallback.onConnectionStateChange(
            oldGatt,
            BluetoothGatt.GATT_SUCCESS,
            BluetoothProfile.STATE_DISCONNECTED
        )

        // Stale disconnect must be dropped and NOT notify listener
        assertEquals(0, listener.disconnectedCount)

        // 4. Legitimate disconnect callback from newGatt runs
        gattLink.gattCallback.onConnectionStateChange(
            newGatt,
            BluetoothGatt.GATT_SUCCESS,
            BluetoothProfile.STATE_DISCONNECTED
        )

        // Legitimate disconnect must notify listener
        assertEquals(1, listener.disconnectedCount)
    }

    @Test
    fun testStaleServicesDiscoveredAndReadsIgnored() {
        val listener = RecordingListener()
        val gattLink = GattLink(
            listener = listener,
            post = { it.run() }
        )

        val oldGatt = createFakeGatt()
        val newGatt = createFakeGatt()

        gattLink.bluetoothGatt = newGatt

        // Stale services discovery from oldGatt
        gattLink.gattCallback.onServicesDiscovered(oldGatt, BluetoothGatt.GATT_SUCCESS)
        assertEquals(0, listener.servicesDiscoveredCount)

        // Stale read callback from oldGatt
        val charCtor = BluetoothGattCharacteristic::class.java.getDeclaredConstructor(
            UUID::class.java, Int::class.javaPrimitiveType, Int::class.javaPrimitiveType
        )
        charCtor.isAccessible = true
        val char = charCtor.newInstance(UUID.randomUUID(), 0, 0)

        gattLink.gattCallback.onCharacteristicRead(oldGatt, char, byteArrayOf(1, 2, 3), BluetoothGatt.GATT_SUCCESS)
        assertEquals(0, listener.readResultCount)
    }
}
