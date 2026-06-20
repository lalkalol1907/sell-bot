package com.sellbot.core.http.auth

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test
import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class TelegramAuthTest {
    private val botToken = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    @Test
    fun `validateInitData accepts valid init data`() {
        val initData = buildInitData(42)
        val user = TelegramAuth.validateInitData(initData, botToken)
        assertNotNull(user)
        assertEquals(42, user?.id)
    }

    @Test
    fun `validateInitData rejects tampered hash`() {
        assertNull(TelegramAuth.validateInitData("${buildInitData(42)}x", botToken))
    }

    @Test
    fun `validateLoginWidget accepts valid login widget payload`() {
        val user = TelegramAuth.validateLoginWidget(buildWidgetParams(99), botToken)
        assertNotNull(user)
        assertEquals(99, user?.id)
    }

    private fun buildInitData(userId: Long): String {
        val user = """{"id":$userId,"first_name":"Test"}"""
        val authDate = (System.currentTimeMillis() / 1000).toString()
        val params = linkedMapOf("auth_date" to authDate, "user" to user)
        val dataCheckString = params.entries
            .sortedBy { it.key }
            .joinToString("\n") { "${it.key}=${it.value}" }
        val secretKey = hmacSha256("WebAppData".toByteArray(), botToken.toByteArray())
        val hash = hmacSha256Hex(secretKey, dataCheckString.toByteArray())
        return "auth_date=$authDate&user=${java.net.URLEncoder.encode(user, Charsets.UTF_8)}&hash=$hash"
    }

    private fun buildWidgetParams(userId: Long): Map<String, Any> {
        val authDate = System.currentTimeMillis() / 1000
        val params = linkedMapOf<String, Any>(
            "id" to userId,
            "first_name" to "Test",
            "auth_date" to authDate,
        )
        val dataCheckString = params.entries
            .sortedBy { it.key }
            .joinToString("\n") { "${it.key}=${it.value}" }
        val secretKey = MessageDigest.getInstance("SHA-256").digest(botToken.toByteArray())
        val hash = hmacSha256Hex(secretKey, dataCheckString.toByteArray())
        return params + ("hash" to hash)
    }

    private fun hmacSha256(key: ByteArray, data: ByteArray): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        return mac.doFinal(data)
    }

    private fun hmacSha256Hex(key: ByteArray, data: ByteArray): String =
        hmacSha256(key, data).joinToString("") { "%02x".format(it) }
}
