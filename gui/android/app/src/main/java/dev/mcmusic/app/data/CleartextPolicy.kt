package dev.mcmusic.app.data

import java.net.Inet4Address
import java.net.InetAddress
import java.net.URI
import java.util.Locale

/**
 * Decide whether an `http://` URL may be opened.
 *
 * Android `<domain>` rules cannot express CIDR ranges, so
 * network_security_config.xml lets the OS permit cleartext and every mcmusic
 * connection must be checked here. The check is purely syntactic: it never
 * resolves DNS, so it cannot block the main thread, and the address that was
 * checked is the literal address the connection will use. Hostnames are limited
 * to `localhost` and `*.local`.
 *
 * HTTPS is always allowed; certificate validation stays with the OS.
 */
object CleartextPolicy {
    /**
     * Throw unless the URL is HTTPS or its host is a private IP literal,
     * `localhost`, or a `.local` name.
     */
    fun requireAllowed(url: String) {
        val uri = URI(url)
        if (!uri.scheme.equals("http", ignoreCase = true)) return
        val host = uri.host ?: throw SecurityException("HTTP URL without a host: $url")
        if (isAllowedHost(host)) return
        throw SecurityException(
            "Cleartext HTTP is only allowed on localhost, *.local and private networks: $url"
        )
    }

    /** Check *url* and return it unchanged, for central URL builders. */
    fun check(url: String): String {
        requireAllowed(url)
        return url
    }

    /** True for a hostname we accept without resolving it. */
    fun isAllowedHost(host: String): Boolean {
        if (host.isEmpty() || host.length > 253) return false
        val lower = host.lowercase(Locale.ROOT).removeSuffix(".")
        if (lower == "localhost" || lower.endsWith(".local")) return true
        val bytes = ipLiteral(lower) ?: return false
        return isPrivate(bytes)
    }

    private fun isPrivate(bytes: ByteArray): Boolean {
        val address = InetAddress.getByAddress(bytes)
        if (address.isLoopbackAddress || address.isLinkLocalAddress ||
            address.isSiteLocalAddress
        ) return true
        if (address is Inet4Address) {
            val v4 = address.address
            val first = v4[0].toInt() and 0xff
            val second = v4[1].toInt() and 0xff
            // 100.64.0.0/10: CGNAT, used by Tailscale. isSiteLocalAddress
            // does not include it, so self-hosters would otherwise regress.
            return first == 100 && (second and 0xc0) == 0x40
        }
        // fc00::/7: IPv6 unique local addresses. Java only knows fec0::/10.
        val first = bytes[0].toInt() and 0xff
        return (first and 0xfe) == 0xfc
    }

    /** Parse an IP literal without a DNS lookup; null means "not an IP". */
    private fun ipLiteral(host: String): ByteArray? {
        if (host.startsWith("[")) {
            if (!host.endsWith("]")) return null
            return ipv6Bytes(host.substring(1, host.length - 1))
        }
        return ipv4Bytes(host) ?: ipv6Bytes(host)
    }

    private fun ipv4Bytes(host: String): ByteArray? {
        val parts = host.split('.')
        if (parts.size != 4) return null
        val bytes = ByteArray(4)
        for (index in parts.indices) {
            val part = parts[index]
            if (part.isEmpty() || part.length > 3 || !part.all { it in '0'..'9' }) return null
            val value = part.toIntOrNull() ?: return null
            if (value > 255) return null
            bytes[index] = value.toByte()
        }
        return bytes
    }

    private fun ipv6Bytes(host: String): ByteArray? {
        if (host.count { it == ':' } < 2) return null
        if (host.any { it !in '0'..'9' && it !in 'a'..'f' && it != ':' && it != '.' }) {
            return null
        }
        val compression = host.indexOf("::")
        if (compression >= 0 && host.indexOf("::", compression + 2) >= 0) return null
        val left = if (compression < 0) host else host.substring(0, compression)
        val right = if (compression < 0) "" else host.substring(compression + 2)

        fun groups(part: String): List<Int>? {
            if (part.isEmpty()) return emptyList()
            val result = mutableListOf<Int>()
            val pieces = part.split(':')
            for ((index, piece) in pieces.withIndex()) {
                if (piece.isEmpty() || piece.length > 4) return null
                if (piece.contains('.')) {
                    // An embedded IPv4 address is only legal as the tail.
                    if (index != pieces.lastIndex) return null
                    val v4 = ipv4Bytes(piece) ?: return null
                    result.add(((v4[0].toInt() and 0xff) shl 8) or (v4[1].toInt() and 0xff))
                    result.add(((v4[2].toInt() and 0xff) shl 8) or (v4[3].toInt() and 0xff))
                } else {
                    val value = piece.toIntOrNull(16) ?: return null
                    result.add(value)
                }
            }
            return result
        }

        val first = groups(left) ?: return null
        val last = groups(right) ?: return null
        val count = first.size + last.size
        if (compression < 0) {
            if (count != 8) return null
        } else if (count >= 8) return null // "::" must compress at least one group

        val bytes = ByteArray(16)
        for (index in first.indices) {
            val at = index * 2
            bytes[at] = (first[index] ushr 8).toByte()
            bytes[at + 1] = first[index].toByte()
        }
        val offset = 8 - last.size
        for (index in last.indices) {
            val at = (offset + index) * 2
            bytes[at] = (last[index] ushr 8).toByte()
            bytes[at + 1] = last[index].toByte()
        }
        return bytes
    }
}
