package rewatch.c900.app

import org.junit.Assert.assertEquals
import org.junit.Test

class NotificationMapperTest {

    @Test
    fun testAllKnownApplicationsMapToCorrectType() {
        assertEquals(NotificationMapper.TYPE_SMS, NotificationMapper.mapPackage("com.android.mms"))
        assertEquals(NotificationMapper.TYPE_SMS, NotificationMapper.mapPackage("com.google.android.apps.messaging"))
        assertEquals(NotificationMapper.TYPE_SMS, NotificationMapper.mapPackage("com.samsung.android.messaging"))

        assertEquals(NotificationMapper.TYPE_QQ, NotificationMapper.mapPackage("com.tencent.mobileqq"))
        assertEquals(NotificationMapper.TYPE_QQ, NotificationMapper.mapPackage("com.tencent.qqlite"))

        assertEquals(NotificationMapper.TYPE_WECHAT, NotificationMapper.mapPackage("com.tencent.mm"))
        assertEquals(NotificationMapper.TYPE_WECHAT, NotificationMapper.mapPackage("com.taobao.qianniu"))

        assertEquals(NotificationMapper.TYPE_FACEBOOK, NotificationMapper.mapPackage("com.facebook.katana"))
        assertEquals(NotificationMapper.TYPE_TWITTER, NotificationMapper.mapPackage("com.twitter.android"))
        assertEquals(NotificationMapper.TYPE_SKYPE, NotificationMapper.mapPackage("com.skype.raider"))
        assertEquals(NotificationMapper.TYPE_LINE, NotificationMapper.mapPackage("jp.naver.line.android"))

        assertEquals(NotificationMapper.TYPE_WHATSAPP, NotificationMapper.mapPackage("com.whatsapp"))
        assertEquals(NotificationMapper.TYPE_WHATSAPP, NotificationMapper.mapPackage("com.whatsapp.w4b"))

        assertEquals(NotificationMapper.TYPE_KAKAOTALK, NotificationMapper.mapPackage("com.kakao.talk"))
        assertEquals(NotificationMapper.TYPE_INSTAGRAM, NotificationMapper.mapPackage("com.instagram.android"))
        assertEquals(NotificationMapper.TYPE_VIBER, NotificationMapper.mapPackage("com.viber.voip"))
        assertEquals(NotificationMapper.TYPE_ZALO, NotificationMapper.mapPackage("com.zing.zalo"))

        assertEquals(NotificationMapper.TYPE_DINGTALK, NotificationMapper.mapPackage("com.alibaba.android.rimet"))
        assertEquals(NotificationMapper.TYPE_WEIBO, NotificationMapper.mapPackage("com.sina.weibo"))
        assertEquals(NotificationMapper.TYPE_ALIPAY, NotificationMapper.mapPackage("com.eg.android.AlipayGphone"))
        assertEquals(NotificationMapper.TYPE_TEAMS, NotificationMapper.mapPackage("com.microsoft.teams"))
        assertEquals(NotificationMapper.TYPE_SNAPCHAT, NotificationMapper.mapPackage("com.snapchat.android"))
        assertEquals(NotificationMapper.TYPE_MESSENGER, NotificationMapper.mapPackage("com.facebook.orca"))
        assertEquals(NotificationMapper.TYPE_LINKEDIN, NotificationMapper.mapPackage("com.linkedin.android"))
        assertEquals(NotificationMapper.TYPE_TELEGRAM, NotificationMapper.mapPackage("org.telegram.messenger"))
        assertEquals(NotificationMapper.TYPE_VK, NotificationMapper.mapPackage("com.vkontakte.android"))
        assertEquals(NotificationMapper.TYPE_OUTLOOK, NotificationMapper.mapPackage("com.microsoft.office.outlook"))
    }

    @Test
    fun testUnmappedApplicationsMapToIgnoreByDefault() {
        assertEquals(false, NotificationMapper.PUSH_UNMAPPED)
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("com.spotify.music"))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("org.mozilla.firefox"))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("com.github.android"))
    }

    @Test
    fun testUnmappedApplicationsMapToOtherWhenEnabled() {
        assertEquals(NotificationMapper.TYPE_OTHER, NotificationMapper.mapPackage("com.spotify.music", pushUnmapped = true))
        assertEquals(NotificationMapper.TYPE_OTHER, NotificationMapper.mapPackage("org.mozilla.firefox", pushUnmapped = true))
        assertEquals(NotificationMapper.TYPE_OTHER, NotificationMapper.mapPackage("com.github.android", pushUnmapped = true))
        assertEquals(13, NotificationMapper.TYPE_OTHER)
    }

    @Test
    fun testIgnoredAndEmptyPackagesReturnNegativeOne() {
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage(null))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage(""))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("   "))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("android"))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("com.android.systemui"))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("rewatch.c900.app"))
        assertEquals(NotificationMapper.TYPE_IGNORE, NotificationMapper.mapPackage("com.myled.hiwearplus"))
    }
}
