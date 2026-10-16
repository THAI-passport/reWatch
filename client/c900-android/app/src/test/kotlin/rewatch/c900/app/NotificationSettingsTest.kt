package rewatch.c900.app

import android.content.SharedPreferences
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NotificationSettingsTest {

    private class FakePreferences : SharedPreferences {
        private val data = mutableMapOf<String, Any>()

        override fun getAll(): MutableMap<String, *> = data
        override fun getString(key: String?, defValue: String?): String? = (data[key] as? String) ?: defValue
        @Suppress("UNCHECKED_CAST")
        override fun getStringSet(key: String?, defValues: MutableSet<String>?): MutableSet<String>? =
            (data[key] as? MutableSet<String>) ?: defValues
        override fun getInt(key: String?, defValue: Int): Int = (data[key] as? Int) ?: defValue
        override fun getLong(key: String?, defValue: Long): Long = (data[key] as? Long) ?: defValue
        override fun getFloat(key: String?, defValue: Float): Float = (data[key] as? Float) ?: defValue
        override fun getBoolean(key: String?, defValue: Boolean): Boolean = (data[key] as? Boolean) ?: defValue
        override fun contains(key: String?): Boolean = data.containsKey(key)
        override fun registerOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}
        override fun unregisterOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}

        override fun edit(): SharedPreferences.Editor = FakeEditor(this)

        class FakeEditor(private val parent: FakePreferences) : SharedPreferences.Editor {
            private val pending = mutableMapOf<String, Any?>()
            private var clearFlag = false

            override fun putString(key: String?, value: String?): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putStringSet(key: String?, values: MutableSet<String>?): SharedPreferences.Editor { pending[key!!] = values; return this }
            override fun putInt(key: String?, value: Int): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putLong(key: String?, value: Long): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putFloat(key: String?, value: Float): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putBoolean(key: String?, value: Boolean): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun remove(key: String?): SharedPreferences.Editor { pending[key!!] = null; return this }
            override fun clear(): SharedPreferences.Editor { clearFlag = true; return this }
            override fun commit(): Boolean { apply(); return true }
            override fun apply() {
                if (clearFlag) parent.data.clear()
                for ((k, v) in pending) {
                    if (v == null) parent.data.remove(k) else parent.data[k] = v
                }
            }
        }
    }

    @Test
    fun testPushOtherAppsDefaultsToFalse() {
        val prefs = FakePreferences()
        val settings = NotificationSettings(prefs)
        assertFalse(settings.pushOtherApps)
    }

    @Test
    fun testPushOtherAppsTogglePersists() {
        val prefs = FakePreferences()
        val settings = NotificationSettings(prefs)

        settings.pushOtherApps = true
        assertTrue(settings.pushOtherApps)

        settings.pushOtherApps = false
        assertFalse(settings.pushOtherApps)
    }

    @Test
    fun testKnownTypesDefaultToEnabled() {
        val prefs = FakePreferences()
        val settings = NotificationSettings(prefs)

        assertTrue(settings.isTypeEnabled(NotificationMapper.TYPE_SMS))
        assertTrue(settings.isTypeEnabled(NotificationMapper.TYPE_WECHAT))
        assertTrue(settings.isTypeEnabled(NotificationMapper.TYPE_WHATSAPP))
        assertTrue(settings.isTypeEnabled(NotificationMapper.TYPE_TELEGRAM))
    }

    @Test
    fun testPerTypeTogglePersists() {
        val prefs = FakePreferences()
        val settings = NotificationSettings(prefs)

        settings.setTypeEnabled(NotificationMapper.TYPE_FACEBOOK, false)
        assertFalse(settings.isTypeEnabled(NotificationMapper.TYPE_FACEBOOK))

        settings.setTypeEnabled(NotificationMapper.TYPE_FACEBOOK, true)
        assertTrue(settings.isTypeEnabled(NotificationMapper.TYPE_FACEBOOK))
    }

    @Test
    fun testTypeIgnoreAlwaysDisabled() {
        val prefs = FakePreferences()
        val settings = NotificationSettings(prefs)
        assertFalse(settings.isTypeEnabled(NotificationMapper.TYPE_IGNORE))
    }
}
