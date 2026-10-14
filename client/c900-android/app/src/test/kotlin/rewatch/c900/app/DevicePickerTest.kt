package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DevicePickerTest {

    @Test
    fun testTargetDeviceNameMatchesFacts() {
        assertEquals("Watch Ultra", MainActivity.TARGET_DEVICE_NAME)
    }

    @Test
    fun testDeviceNameMatchingFiltersToWatchUltra() {
        assertTrue(MainActivity.isMatchingDevice("Watch Ultra"))
        assertTrue(MainActivity.isMatchingDevice("watch ultra"))
        assertTrue(MainActivity.isMatchingDevice("  Watch Ultra  "))

        assertFalse(MainActivity.isMatchingDevice("Apple Watch"))
        assertFalse(MainActivity.isMatchingDevice("C900"))
        assertFalse(MainActivity.isMatchingDevice("Hiwear Plus"))
        assertFalse(MainActivity.isMatchingDevice(null))
        assertFalse(MainActivity.isMatchingDevice(""))
        assertFalse(MainActivity.isMatchingDevice("   "))
    }

    @Test
    fun testManufacturerDataMatchingWithMarker() {
        val validMfg = byteArrayOf(0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x12, 0x34)
        assertTrue(MainActivity.isMatchingDevice(null, validMfg))
        assertTrue(MainActivity.isMatchingDevice("Unknown", validMfg))

        val invalidMarker = byteArrayOf(0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x12, 0x35)
        assertFalse(MainActivity.isMatchingDevice(null, invalidMarker))

        val shortMfg = byteArrayOf(0x12, 0x34)
        assertFalse(MainActivity.isMatchingDevice(null, shortMfg))
    }
}
