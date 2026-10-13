package rewatch.c900.app

/**
 * Package-to-type mapping for notification push (cmd 0x02 key 18).
 * Based on C900-Q04 section 5 and FACTS section 5 (new type table for feature byte 15 bit 0x02 set).
 * Unmapped applications return 13 (Other). Ignored system apps return -1 (dropped).
 */
object NotificationMapper {
    const val TYPE_IGNORE = -1
    const val TYPE_SMS = 1
    const val TYPE_QQ = 2
    const val TYPE_WECHAT = 3
    const val TYPE_FACEBOOK = 4
    const val TYPE_TWITTER = 5
    const val TYPE_SKYPE = 6
    const val TYPE_LINE = 7
    const val TYPE_WHATSAPP = 8
    const val TYPE_KAKAOTALK = 9
    const val TYPE_INSTAGRAM = 10
    const val TYPE_VIBER = 11
    const val TYPE_ZALO = 12
    const val TYPE_OTHER = 13
    const val TYPE_DINGTALK = 14
    const val TYPE_WEIBO = 15
    const val TYPE_ALIPAY = 16
    const val TYPE_TEAMS = 17
    const val TYPE_SNAPCHAT = 18
    const val TYPE_MESSENGER = 19
    const val TYPE_LINKEDIN = 20
    const val TYPE_TELEGRAM = 21
    const val TYPE_VK = 22
    const val TYPE_OUTLOOK = 23

    private val IGNORED_PACKAGES = setOf(
        "android",
        "com.android.systemui",
        "rewatch.c900.app",
        "com.myled.hiwearplus"
    )

    private val PACKAGE_MAP = mapOf(
        // SMS (1)
        "com.android.mms" to TYPE_SMS,
        "com.google.android.apps.messaging" to TYPE_SMS,
        "com.samsung.android.messaging" to TYPE_SMS,
        "com.android.mms.service" to TYPE_SMS,

        // QQ (2)
        "com.tencent.mobileqq" to TYPE_QQ,
        "com.tencent.qqlite" to TYPE_QQ,
        "com.tencent.timtim" to TYPE_QQ,

        // WeChat (3)
        "com.tencent.mm" to TYPE_WECHAT,
        "com.taobao.qianniu" to TYPE_WECHAT,

        // Facebook (4)
        "com.facebook.katana" to TYPE_FACEBOOK,

        // Twitter / X (5)
        "com.twitter.android" to TYPE_TWITTER,

        // Skype (6)
        "com.skype.raider" to TYPE_SKYPE,

        // LINE (7)
        "jp.naver.line.android" to TYPE_LINE,

        // WhatsApp (8)
        "com.whatsapp" to TYPE_WHATSAPP,
        "com.whatsapp.w4b" to TYPE_WHATSAPP,

        // KakaoTalk (9)
        "com.kakao.talk" to TYPE_KAKAOTALK,

        // Instagram (10)
        "com.instagram.android" to TYPE_INSTAGRAM,

        // Viber (11)
        "com.viber.voip" to TYPE_VIBER,

        // Zalo (12)
        "com.zing.zalo" to TYPE_ZALO,

        // DingTalk (14)
        "com.alibaba.android.rimet" to TYPE_DINGTALK,

        // Weibo (15)
        "com.sina.weibo" to TYPE_WEIBO,

        // Alipay (16)
        "com.eg.android.alipaygphone" to TYPE_ALIPAY,

        // Teams (17)
        "com.microsoft.teams" to TYPE_TEAMS,

        // Snapchat (18)
        "com.snapchat.android" to TYPE_SNAPCHAT,

        // Messenger (19)
        "com.facebook.orca" to TYPE_MESSENGER,

        // LinkedIn (20)
        "com.linkedin.android" to TYPE_LINKEDIN,

        // Telegram (21)
        "org.telegram.messenger" to TYPE_TELEGRAM,

        // VK (22)
        "com.vkontakte.android" to TYPE_VK,

        // Outlook (23)
        "com.microsoft.office.outlook" to TYPE_OUTLOOK
    )

    /**
     * Map package name to notification type code.
     * Returns -1 if package should be ignored, or 13 (Other) if unmapped.
     */
    fun mapPackage(packageName: String?): Int {
        if (packageName.isNullOrBlank()) return TYPE_IGNORE
        val pkg = packageName.trim().lowercase()
        if (pkg in IGNORED_PACKAGES) return TYPE_IGNORE
        return PACKAGE_MAP[pkg] ?: TYPE_OTHER
    }
}
