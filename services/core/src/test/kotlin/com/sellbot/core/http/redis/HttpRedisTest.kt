package com.sellbot.core.http.redis

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class LoginRoutingTest {
    @Test
    fun `pickEngineAddress round-robin uses all engines`() {
        val addrs = listOf("a", "b", "c")
        val picked = (0 until 10).map { LoginRouting.pickEngineAddress(addrs, 0, it) }
        assertEquals(addrs.sorted(), picked.toSet().sorted())
    }
}

class LoginHandoffUrlTest {
    @Test
    fun `buildLoginHandoffUrl appends handoff query param`() {
        val url = LoginHandoff.buildLoginHandoffUrl("https://login.example.com/miniapp/", "abc123")
        assertEquals("https://login.example.com/miniapp/?handoff=abc123", url)
    }

    @Test
    fun `buildLoginHandoffUrl preserves existing query params`() {
        val url = LoginHandoff.buildLoginHandoffUrl("https://login.example.com/miniapp/?x=1", "abc123")
        assertEquals("https://login.example.com/miniapp/?x=1&handoff=abc123", url)
    }
}
