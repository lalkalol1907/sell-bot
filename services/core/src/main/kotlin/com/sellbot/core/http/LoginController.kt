package com.sellbot.core.http

import com.sellbot.core.http.dto.toDto
import com.sellbot.core.http.grpc.WorkerLoginClient
import com.sellbot.core.http.redis.LoginEnginePool
import com.sellbot.core.http.redis.LoginRouting
import com.sellbot.core.http.redis.RateLimiter
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/v1/login")
class LoginController(
    private val workerLoginClient: WorkerLoginClient,
    private val rateLimiter: RateLimiter,
    private val loginRouting: LoginRouting,
    private val loginEnginePool: LoginEnginePool,
) {

    @PostMapping("/session")
    fun session(request: jakarta.servlet.http.HttpServletRequest) =
        mapOf("seller_id" to request.sellerId())

    @PostMapping("/qr/start")
    fun startQr(request: jakarta.servlet.http.HttpServletRequest): ResponseEntity<Any> {
        val sellerId = request.sellerId()
        val engineAddr = loginEnginePool.pickForNewSession(sellerId.toInt())
        val step = workerLoginClient.startQrLogin(engineAddr, sellerId)
        if (step.loginId.isNotBlank()) {
            loginRouting.pin(step.loginId, engineAddr)
        }
        return ResponseEntity.ok(step.toDto())
    }

    @PostMapping("/phone/start")
    fun startPhone(
        request: jakarta.servlet.http.HttpServletRequest,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val actorKey = loginActorKey(request)
        if (!rateLimiter.allow("phone:$actorKey", 5, 60_000)) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body(mapOf("error" to "rate limit exceeded"))
        }

        val phone = normalizePhone(body["phone"]?.toString() ?: "")
        if (!validPhone(phone)) {
            return ResponseEntity.badRequest().body(mapOf("error" to "invalid phone"))
        }

        val sellerId = request.sellerId()
        val engineAddr = loginEnginePool.pickForNewSession(sellerId.toInt())
        val step = workerLoginClient.startPhoneLogin(engineAddr, sellerId, phone)
        if (step.loginId.isNotBlank()) {
            loginRouting.pin(step.loginId, engineAddr)
        }
        return ResponseEntity.ok(step.toDto())
    }

    @PostMapping("/{loginId}/code")
    fun submitCode(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable loginId: String,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val actorKey = loginActorKey(request)
        if (!rateLimiter.allow("code:$actorKey", 10, 60_000)) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body(mapOf("error" to "rate limit exceeded"))
        }

        val code = body["code"]?.toString()?.replace("\\s+".toRegex(), "") ?: ""
        if (code.isBlank()) {
            return ResponseEntity.badRequest().body(mapOf("error" to "code required"))
        }

        return withPinnedClient(loginId) { engineAddr ->
            val step = workerLoginClient.submitCode(engineAddr, loginId, code)
            clearRouteIfDone(step.status, loginId)
            ResponseEntity.ok(step.toDto())
        }
    }

    @PostMapping("/{loginId}/password")
    fun submitPassword(
        @PathVariable loginId: String,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val password = body["password"]?.toString() ?: ""
        if (password.isBlank()) {
            return ResponseEntity.badRequest().body(mapOf("error" to "password required"))
        }

        return withPinnedClient(loginId) { engineAddr ->
            val step = workerLoginClient.submitPassword(engineAddr, loginId, password)
            clearRouteIfDone(step.status, loginId)
            ResponseEntity.ok(step.toDto())
        }
    }

    @GetMapping("/{loginId}/status")
    fun loginStatus(@PathVariable loginId: String): ResponseEntity<Any> =
        withPinnedClient(loginId) { engineAddr ->
            val step = workerLoginClient.getLoginStatus(engineAddr, loginId)
            clearRouteIfDone(step.status, loginId)
            ResponseEntity.ok(step.toDto())
        }

    private fun withPinnedClient(
        loginId: String,
        fn: (String) -> ResponseEntity<Any>,
    ): ResponseEntity<Any> {
        val engineAddr = loginRouting.resolve(loginId)
            ?: return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(mapOf("error" to "login session expired, start again"))
        return fn(engineAddr)
    }

    private fun clearRouteIfDone(status: String, loginId: String) {
        if (status == "success" || status == "error") {
            loginRouting.clear(loginId)
        }
    }

    private fun validPhone(phone: String): Boolean =
        Regex("^\\+?\\d{10,15}$").matches(phone)

    private fun normalizePhone(raw: String): String {
        val trimmed = raw.trim()
        return if (trimmed.startsWith("+")) trimmed else "+$trimmed"
    }
}
