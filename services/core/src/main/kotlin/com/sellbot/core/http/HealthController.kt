package com.sellbot.core.http

import org.springframework.http.MediaType
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController
import com.sellbot.core.http.redis.LoginEnginePool

@RestController
class HealthController(
    private val loginEnginePool: LoginEnginePool,
) {
    @GetMapping("/health")
    fun health() = mapOf(
        "status" to "ok",
        "login_engines" to loginEnginePool.size,
    )

    @GetMapping("/metrics", produces = [MediaType.TEXT_PLAIN_VALUE])
    fun metrics(): String =
        "# HELP core_up Core HTTP API is running\n# TYPE core_up gauge\ncore_up 1\n"
}
