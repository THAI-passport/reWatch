package rewatch.c900.app

import android.content.Context
import android.content.SharedPreferences

/**
 * Persisted notification push preferences stored in [SharedPreferences].
 *
 * Controls whether unmapped applications are pushed ("push other apps", off by default)
 * and whether individual notification types are forwarded to the watch.
 */
class NotificationSettings(private val prefs: SharedPreferences) {

    /**
     * Replaces the static PUSH_UNMAPPED constant with a user preference.
     * Off by default to avoid write flood and flash wear (ground rule 7).
     * Vendor pushes "other" only when explicitly user-enabled (MsgPushHelper.getShowOtherNotify [C]).
     */
    var pushOtherApps: Boolean
        get() = prefs.getBoolean(KEY_PUSH_OTHER, false)
        set(value) {
            prefs.edit().putBoolean(KEY_PUSH_OTHER, value).apply()
        }

    /**
     * Checks if a notification type code is enabled.
     * Mapped types default to true (enabled).
     */
    fun isTypeEnabled(type: Int): Boolean {
        if (type == NotificationMapper.TYPE_IGNORE) return false
        return prefs.getBoolean(keyForType(type), true)
    }

    /**
     * Enables or disables a specific notification type.
     */
    fun setTypeEnabled(type: Int, enabled: Boolean) {
        prefs.edit().putBoolean(keyForType(type), enabled).apply()
    }

    companion object {
        const val PREFS_NAME = "rewatch_notification_settings"
        const val KEY_PUSH_OTHER = "push_other_apps"

        fun keyForType(type: Int): String = "type_enabled_$type"

        fun fromContext(context: Context): NotificationSettings {
            return NotificationSettings(
                context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            )
        }

        val KNOWN_TYPES = listOf(
            NotificationMapper.TYPE_SMS to "SMS / Messaging",
            NotificationMapper.TYPE_QQ to "QQ",
            NotificationMapper.TYPE_WECHAT to "WeChat",
            NotificationMapper.TYPE_FACEBOOK to "Facebook",
            NotificationMapper.TYPE_TWITTER to "Twitter / X",
            NotificationMapper.TYPE_SKYPE to "Skype",
            NotificationMapper.TYPE_LINE to "LINE",
            NotificationMapper.TYPE_WHATSAPP to "WhatsApp",
            NotificationMapper.TYPE_KAKAOTALK to "KakaoTalk",
            NotificationMapper.TYPE_INSTAGRAM to "Instagram",
            NotificationMapper.TYPE_VIBER to "Viber",
            NotificationMapper.TYPE_ZALO to "Zalo",
            NotificationMapper.TYPE_DINGTALK to "DingTalk",
            NotificationMapper.TYPE_WEIBO to "Weibo",
            NotificationMapper.TYPE_ALIPAY to "Alipay",
            NotificationMapper.TYPE_TEAMS to "Microsoft Teams",
            NotificationMapper.TYPE_SNAPCHAT to "Snapchat",
            NotificationMapper.TYPE_MESSENGER to "Messenger",
            NotificationMapper.TYPE_LINKEDIN to "LinkedIn",
            NotificationMapper.TYPE_TELEGRAM to "Telegram",
            NotificationMapper.TYPE_VK to "VK",
            NotificationMapper.TYPE_OUTLOOK to "Outlook",
            NotificationMapper.TYPE_OTHER to "Other Applications"
        )
    }
}
