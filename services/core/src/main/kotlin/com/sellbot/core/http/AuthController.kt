package com.sellbot.core.http

import com.sellbot.core.http.auth.JWT_COOKIE_NAME
import com.sellbot.core.http.auth.JwtSession
import com.sellbot.core.http.auth.TelegramAuth
import com.sellbot.core.http.dto.toDto
import com.sellbot.core.service.CatalogService
import com.sellbot.core.service.TeamService
import jakarta.servlet.http.HttpServletResponse
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseCookie
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/v1/auth")
class AuthController(
    private val properties: SellbotHttpProperties,
    private val catalogService: CatalogService,
    private val teamService: TeamService,
    private val jwtSession: JwtSession,
) {

    @PostMapping("/telegram")
    fun telegramLogin(
        @RequestBody body: Map<String, Any?>,
        response: HttpServletResponse,
    ): ResponseEntity<Any> {
        val user = TelegramAuth.validateLoginWidget(body, properties.botToken)
            ?: return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(mapOf("error" to "invalid telegram auth"))

        val access = teamService.resolveDashboardAccess(user.id)
            ?: return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(mapOf("error" to "seller not found, run /start in bot first"))

        val token = jwtSession.encode(access.seller.id!!, user.id)
        setJwtCookie(response, token)
        return ResponseEntity.ok(access.seller.toDto(isOwner = access.isOwner))
    }

    @PostMapping("/logout")
    fun logout(response: HttpServletResponse): ResponseEntity<Void> {
        clearJwtCookie(response)
        return ResponseEntity.noContent().build()
    }

    @GetMapping("/me")
    fun me(request: jakarta.servlet.http.HttpServletRequest): ResponseEntity<Any> {
        return try {
            val seller = catalogService.getSeller(request.sellerId())
            val isOwner = teamService.isOwner(seller.id!!, request.tgUserId())
            ResponseEntity.ok(seller.toDto(isOwner = isOwner))
        } catch (_: Exception) {
            ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("error" to "unauthorized"))
        }
    }

    private fun setJwtCookie(response: HttpServletResponse, token: String) {
        val cookie = ResponseCookie.from(JWT_COOKIE_NAME, token)
            .httpOnly(true)
            .secure(properties.secureCookies)
            .path("/")
            .sameSite("Lax")
            .maxAge(properties.jwt.ttlHours * 3600)
            .build()
        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString())
    }

    private fun clearJwtCookie(response: HttpServletResponse) {
        val cookie = ResponseCookie.from(JWT_COOKIE_NAME, "")
            .httpOnly(true)
            .secure(properties.secureCookies)
            .path("/")
            .sameSite("Lax")
            .maxAge(0)
            .build()
        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString())
    }
}
