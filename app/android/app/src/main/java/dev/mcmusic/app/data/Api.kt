package dev.mcmusic.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class ApiException(message: String, val status: Int = 0) : Exception(message)

/**
 * Thin JSON client over the mcmusic API. Auth is the session cookie; no token
 * ever reaches or leaves the client.
 */
class Api(private val store: SessionStore) {

    private val jsonType = "application/json; charset=utf-8".toMediaType()

    val client: OkHttpClient = OkHttpClient.Builder()
        .cookieJar(store.cookieJar)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .build()

    @Volatile
    var baseUrl: String = normalize(store.baseUrl)
        private set

    fun setBase(raw: String): String {
        val next = normalize(raw)
        baseUrl = next
        store.baseUrl = next
        return next
    }

    private fun normalize(raw: String): String {
        var v = raw.trim()
        if (v.isEmpty()) return baseUrlOr(default = "http://127.0.0.1:8000")
        if (!v.startsWith("http://") && !v.startsWith("https://")) v = "http://$v"
        v = v.trimEnd('/')
        if (v.endsWith("/api")) v = v.removeSuffix("/api")
        return v
    }

    private fun baseUrlOr(default: String): String =
        if (store.baseUrl.isBlank()) default else store.baseUrl.trimEnd('/')

    fun url(path: String): String =
        if (path.startsWith("http://") || path.startsWith("https://")) path
        else "$baseUrl/api/${path.trimStart('/')}"

    fun coverUrl(id: Int?): String? = id?.let { url("tracks/$it/cover") }

    fun streamUrl(id: Int): String = url("tracks/$id/stream")

    fun cookieHeader(): String = store.cookieJar.header()

    /** Raw body bytes, used by the offline download store. */
    suspend fun bytes(path: String): ByteArray? = withContext(Dispatchers.IO) {
        val builder = Request.Builder().url(url(path)).header("Accept", "*/*")
        val cookie = cookieHeader()
        if (cookie.isNotBlank()) builder.header("Cookie", cookie)
        try {
            client.newCall(builder.get().build()).execute().use { res ->
                if (!res.isSuccessful) null else res.body?.bytes()
            }
        } catch (e: Exception) {
            null
        }
    }

    suspend fun get(path: String, query: Map<String, String> = emptyMap()): JSONObject =
        request("GET", path, null, query)

    suspend fun post(path: String, body: JSONObject? = null): JSONObject =
        request("POST", path, body, emptyMap())

    suspend fun put(path: String, body: JSONObject? = null): JSONObject =
        request("PUT", path, body, emptyMap())

    suspend fun patch(path: String, body: JSONObject? = null): JSONObject =
        request("PATCH", path, body, emptyMap())

    suspend fun delete(path: String): JSONObject =
        request("DELETE", path, null, emptyMap())

    private suspend fun request(
        method: String,
        path: String,
        body: JSONObject?,
        query: Map<String, String>,
    ): JSONObject = withContext(Dispatchers.IO) {
        val builder = url(path).toHttpUrlOrNull()?.newBuilder()
            ?: throw ApiException("Invalid server address")
        query.forEach { (k, v) -> builder.addQueryParameter(k, v) }
        val httpUrl = builder.build()

        val rb = Request.Builder().url(httpUrl).header("Accept", "application/json")
        when (method) {
            "GET" -> rb.get()
            "DELETE" -> rb.delete()
            else -> rb.method(method, body?.toString()?.toRequestBody(jsonType) ?: "".toRequestBody(jsonType))
        }

        try {
            client.newCall(rb.build()).execute().use { res ->
                val text = res.body?.string().orEmpty()
                val json = if (text.isBlank()) JSONObject() else runCatching { JSONObject(text) }
                    .getOrElse { JSONObject().put("error", text.take(200)) }
                if (!res.isSuccessful) {
                    val msg = json.optString("error").ifBlank { "HTTP ${res.code}" }
                    throw ApiException(msg, res.code)
                }
                json
            }
        } catch (e: ApiException) {
            throw e
        } catch (e: java.net.UnknownHostException) {
            throw ApiException("Can't reach the server")
        } catch (e: java.net.ConnectException) {
            throw ApiException("Can't reach the server")
        } catch (e: java.net.SocketTimeoutException) {
            throw ApiException("Server timed out")
        }
    }
}
