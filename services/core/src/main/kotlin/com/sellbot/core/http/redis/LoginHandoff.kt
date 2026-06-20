package com.sellbot.core.http.redis

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import org.springframework.data.redis.core.StringRedisTemplate
import org.springframework.stereotype.Component
import java.net.URI
import java.security.SecureRandom
import java.time.Duration

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class LoginHandoffPayload(
    val sellerId: Long,
    val tgUserId: Long,
)

@Component
class LoginHandoff(
    private val redis: StringRedisTemplate,
    private val objectMapper: ObjectMapper,
) {
    private val random = SecureRandom()

    fun create(sellerId: Long, tgUserId: Long): String {
        val token = random.generateToken()
        val payload = LoginHandoffPayload(sellerId = sellerId, tgUserId = tgUserId)
        redis.opsForValue().set(
            "$HANDOFF_PREFIX$token",
            objectMapper.writeValueAsString(payload),
            HANDOFF_TTL,
        )
        return token
    }

    fun resolve(token: String): LoginHandoffPayload? {
        if (token.isBlank()) return null
        val raw = redis.opsForValue().get("$HANDOFF_PREFIX$token") ?: return null
        return try {
            val payload = objectMapper.readValue<LoginHandoffPayload>(raw)
            if (payload.sellerId == 0L) null else payload
        } catch (_: Exception) {
            null
        }
    }

    companion object {
        private const val HANDOFF_PREFIX = "login:handoff:"
        private val HANDOFF_TTL = Duration.ofMinutes(30)

        fun buildLoginHandoffUrl(baseUrl: String, token: String): String {
            val uri = URI.create(baseUrl)
            val query = buildString {
                if (!uri.rawQuery.isNullOrBlank()) {
                    append(uri.rawQuery)
                    append('&')
                }
                append("handoff=")
                append(token)
            }
            return URI(uri.scheme, uri.authority, uri.path, query, uri.fragment).toString()
        }
    }
}

private fun SecureRandom.generateToken(): String {
    val bytes = ByteArray(32)
    nextBytes(bytes)
    return bytes.joinToString("") { "%02x".format(it) }
}
