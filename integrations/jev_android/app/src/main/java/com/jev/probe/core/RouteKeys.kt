package com.jev.probe.core

import java.net.URI

/** Reuse a key only when both routes have the same scheme, host and port. */
internal object RouteKeys {
    private fun origin(url: String): Triple<String, String, Int>? {
        return try {
            val uri = URI(url.trim())
            val scheme = uri.scheme?.lowercase() ?: return null
            val host = uri.host?.lowercase() ?: return null
            if (scheme != "https" && scheme != "http") return null
            val port = if (uri.port >= 0) uri.port else if (scheme == "https") 443 else 80
            Triple(scheme, host, port)
        } catch (_: Exception) {
            null
        }
    }

    private fun sameOrigin(a: String, b: String): Boolean =
        origin(a)?.let { it == origin(b) } ?: false

    fun reply(replyKey: String, judgeKey: String, replyUrl: String, judgeUrl: String): String =
        replyKey.ifBlank { if (sameOrigin(replyUrl, judgeUrl)) judgeKey else "" }

    fun vision(visionKey: String, replyKey: String, judgeKey: String,
               visionUrl: String, replyUrl: String, judgeUrl: String): String =
        visionKey.ifBlank {
            when {
                sameOrigin(visionUrl, replyUrl) && replyKey.isNotBlank() -> replyKey
                sameOrigin(visionUrl, judgeUrl) -> judgeKey
                else -> ""
            }
        }
}
