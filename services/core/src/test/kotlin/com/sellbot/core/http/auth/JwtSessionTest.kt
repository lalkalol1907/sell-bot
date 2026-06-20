package com.sellbot.core.http.auth

import com.sellbot.core.http.SellbotHttpProperties
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class JwtSessionTest {
    private val jwtSession = JwtSession(
        SellbotHttpProperties(jwt = SellbotHttpProperties.JwtProperties(secret = "test-secret", ttlHours = 1)),
    )

    @Test
    fun `encode and decode round trip`() {
        val token = jwtSession.encode(7, 42)
        val payload = jwtSession.decode(token)
        assertNotNull(payload)
        assertEquals(7, payload?.sellerId)
        assertEquals(42, payload?.tgUserId)
    }

    @Test
    fun `decode returns null for blank token`() {
        assertNull(jwtSession.decode(null))
        assertNull(jwtSession.decode(""))
    }
}
