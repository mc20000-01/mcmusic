package dev.mcmusic.app.data

import java.net.HttpURLConnection
import java.net.URL

/**
 * HttpURLConnection GETs that re-check the cleartext policy on every redirect.
 *
 * Automatic redirect following would let a trusted private URL bounce to a
 * public `http://` host while the OS permits cleartext globally, so the chain
 * is walked here instead. The returned connection is already connected.
 */
object CheckedHttp {
    private const val MAX_REDIRECTS = 5

    fun open(
        initial: String,
        connectTimeout: Int = 10_000,
        readTimeout: Int = 15_000,
        headers: Map<String, String> = emptyMap(),
    ): HttpURLConnection {
        var target = Api.checkedUrl(initial)
        for (attempt in 0..MAX_REDIRECTS) {
            val conn = (URL(target).openConnection() as HttpURLConnection).apply {
                instanceFollowRedirects = false
                this.connectTimeout = connectTimeout
                this.readTimeout = readTimeout
                headers.forEach { (name, value) -> setRequestProperty(name, value) }
            }
            conn.connect()
            val code = conn.responseCode
            if (code in 300..399 && code != 304) {
                val location = conn.getHeaderField("Location")
                conn.disconnect()
                if (location.isNullOrBlank()) return conn
                target = Api.checkedUrl(URL(URL(target), location).toString())
                continue
            }
            return conn
        }
        error("too many redirects while fetching $initial")
    }
}
