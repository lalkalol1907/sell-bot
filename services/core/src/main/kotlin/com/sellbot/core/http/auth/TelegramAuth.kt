package com.sellbot.core.http.auth

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

data class TelegramUser(
    val id: Long,
    val firstName: String? = null,
    val username: String? = null,
)

object TelegramAuth {
    private const val MAX_AGE_SEC = 86_400L
    private val mapper = ObjectMapper()

    fun validateInitData(initData: String, botToken: String): TelegramUser? {
        if (initData.isBlank() || botToken.isBlank()) return null

        val params = parseQuery(initData)
        val hash = params.remove("hash") ?: return null

        val dataCheckString = params.entries
            .sortedBy { it.key }
            .joinToString("\n") { "${it.key}=${it.value}" }

        val secretKey = hmacSha256("WebAppData".toByteArray(), botToken.toByteArray())
        val computed = hmacSha256Hex(secretKey, dataCheckString.toByteArray())
        if (!secureEqual(computed, hash)) return null

        val authDate = params["auth_date"]?.toLongOrNull() ?: 0L
        if (authDate > 0 && currentEpochSec() - authDate > MAX_AGE_SEC) return null

        val userRaw = params["user"] ?: return null
        return try {
            val user = mapper.readValue<Map<String, Any?>>(userRaw)
            val id = (user["id"] as? Number)?.toLong() ?: return null
            TelegramUser(
                id = id,
                firstName = user["first_name"] as? String,
                username = user["username"] as? String,
            )
        } catch (_: Exception) {
            null
        }
    }

    fun validateLoginWidget(payload: Map<String, Any?>, botToken: String): TelegramUser? {
        if (botToken.isBlank()) return null

        val data = linkedMapOf<String, String>()
        for ((key, value) in payload) {
            if (key == "hash" || value == null) continue
            data[key] = value.toString()
        }

        val hash = payload["hash"]?.toString() ?: return null
        if (hash.isBlank()) return null

        val dataCheckString = data.entries
            .sortedBy { it.key }
            .joinToString("\n") { "${it.key}=${it.value}" }

        val secretKey = MessageDigest.getInstance("SHA-256").digest(botToken.toByteArray())
        val computed = hmacSha256Hex(secretKey, dataCheckString.toByteArray())
        if (!secureEqual(computed, hash)) return null

        val authDate = data["auth_date"]?.toLongOrNull() ?: 0L
        if (authDate > 0 && currentEpochSec() - authDate > MAX_AGE_SEC) return null

        val id = data["id"]?.toLongOrNull() ?: return null
        if (id == 0L) return null

        return TelegramUser(id = id, firstName = data["first_name"], username = data["username"])
    }

    private fun parseQuery(query: String): MutableMap<String, String> {
        val result = linkedMapOf<String, String>()
        for (part in query.split("&")) {
            if (part.isBlank()) continue
            val idx = part.indexOf('=')
            if (idx <= 0) continue
            val key = part.substring(0, idx)
            val value = part.substring(idx + 1)
            result[key] = java.net.URLDecoder.decode(value, Charsets.UTF_8)
        }
        return result
    }

    private fun hmacSha256(key: ByteArray, data: ByteArray): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        return mac.doFinal(data)
    }

    private fun hmacSha256Hex(key: ByteArray, data: ByteArray): String =
        hmacSha256(key, data).joinToString("") { "%02x".format(it) }

    private fun secureEqual(a: String, b: String): Boolean {
        val bufA = a.toByteArray()
        val bufB = b.toByteArray()
        if (bufA.size != bufB.size) return false
        return MessageDigest.isEqual(bufA, bufB)
    }

    private fun currentEpochSec(): Long = System.currentTimeMillis() / 1000
}
