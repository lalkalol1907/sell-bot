package com.sellbot.core.http.auth

import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import com.auth0.jwt.exceptions.JWTVerificationException
import org.springframework.stereotype.Component
import com.sellbot.core.http.SellbotHttpProperties
import java.time.Instant
import java.time.temporal.ChronoUnit

const val JWT_COOKIE_NAME = "sellbot_jwt"

data class JwtPayload(
    val sellerId: Long,
    val tgUserId: Long,
)

@Component
class JwtSession(
    properties: SellbotHttpProperties,
) {
    private val secret = properties.jwt.secret
    private val ttlHours = properties.jwt.ttlHours
    private val algorithm = Algorithm.HMAC256(secret)

    fun encode(sellerId: Long, tgUserId: Long): String =
        JWT.create()
            .withClaim("seller_id", sellerId)
            .withClaim("tg_user_id", tgUserId)
            .withExpiresAt(Instant.now().plus(ttlHours, ChronoUnit.HOURS))
            .sign(algorithm)

    fun decode(token: String?): JwtPayload? {
        if (token.isNullOrBlank()) return null
        return try {
            val decoded = JWT.require(algorithm).build().verify(token)
            val sellerId = decoded.getClaim("seller_id").asLong()
            val tgUserId = decoded.getClaim("tg_user_id").asLong()
            if (sellerId == null || sellerId == 0L) return null
            JwtPayload(sellerId = sellerId, tgUserId = tgUserId ?: 0L)
        } catch (_: JWTVerificationException) {
            null
        }
    }
}
