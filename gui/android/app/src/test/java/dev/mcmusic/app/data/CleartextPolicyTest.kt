package dev.mcmusic.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.fail
import org.junit.Test

/** Pure JVM tests: no Android runtime, no DNS, no sockets. */
class CleartextPolicyTest {
    @Test
    fun allowsPrivateAndSelfHostRanges() {
        val allowed = listOf(
            "http://192.168.1.5/api/tracks",
            "http://10.0.0.2/api/tracks",
            "http://10.0.2.2/api/tracks",
            "http://172.16.5.4/api/tracks",
            "http://100.64.1.1/api/tracks",
            "http://127.0.0.1:8000/api/tracks",
            "http://localhost:8000/api/tracks",
            "http://nas.local/api/tracks",
            "http://[::1]:8000/api/tracks",
            "http://[fd00::1]/api/tracks",
            "http://[fe80::1]/api/tracks",
        )
        for (url in allowed) CleartextPolicy.requireAllowed(url)
    }

    @Test
    fun rejectsPublicHttp() {
        val rejected = listOf(
            "http://example.com/api/tracks",
            "http://8.8.8.8/api/tracks",
            "http://[2606:4700:4700::1111]/api/tracks",
            "http://192.168.1.5.example.com/api/tracks",
            "http://999.1.1.1/api/tracks",
            "http://1::2::3/api/tracks",
            "http:///api/tracks",
        )
        for (url in rejected) {
            try {
                CleartextPolicy.requireAllowed(url)
                fail("cleartext URL was accepted: $url")
            } catch (_: SecurityException) {
                // expected
            }
        }
    }

    @Test
    fun httpsAlwaysPasses() {
        val secure = listOf(
            "https://example.com/api/tracks",
            "https://8.8.8.8/api/tracks",
            "https://[2606:4700:4700::1111]/api/tracks",
        )
        for (url in secure) CleartextPolicy.requireAllowed(url)
    }

    @Test
    fun checkReturnsTheSameUrl() {
        val url = "http://100.64.1.1/api/tracks/1/stream"
        assertEquals(url, CleartextPolicy.check(url))
    }
}
