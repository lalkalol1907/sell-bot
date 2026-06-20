package com.sellbot.core.http

import com.sellbot.core.http.auth.JWT_COOKIE_NAME
import com.sellbot.core.http.auth.JwtSession
import com.sellbot.core.http.auth.TelegramAuth
import com.sellbot.core.http.auth.TelegramUser
import com.sellbot.core.http.redis.LoginHandoff
import com.sellbot.core.service.CatalogService
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.servlet.HandlerInterceptor
import com.fasterxml.jackson.databind.ObjectMapper

@Component
class SellerAuthInterceptor(
    private val jwtSession: JwtSession,
) : HandlerInterceptor {

    override fun preHandle(request: HttpServletRequest, response: HttpServletResponse, handler: Any): Boolean {
        val token = readCookie(request, JWT_COOKIE_NAME)
        val session = jwtSession.decode(token)
        if (session == null) {
            writeJsonError(response, HttpStatus.UNAUTHORIZED, "unauthorized")
            return false
        }
        request.setAttribute(HttpSessionAttributes.SELLER_ID, session.sellerId)
        request.setAttribute(HttpSessionAttributes.TG_USER_ID, session.tgUserId)
        return true
    }

    companion object {
        fun readCookie(request: HttpServletRequest, name: String): String? {
            val cookies = request.cookies ?: return null
            return cookies.firstOrNull { it.name == name }?.value
        }

        fun writeJsonError(response: HttpServletResponse, status: HttpStatus, message: String) {
            response.status = status.value()
            response.contentType = MediaType.APPLICATION_JSON_VALUE
            response.writer.write("""{"error":"$message"}""")
        }
    }
}

@Component
class LoginAuthInterceptor(
    private val properties: SellbotHttpProperties,
    private val catalogService: CatalogService,
    private val loginHandoff: LoginHandoff,
    private val objectMapper: ObjectMapper,
) : HandlerInterceptor {

    override fun preHandle(request: HttpServletRequest, response: HttpServletResponse, handler: Any): Boolean {
        val initData = request.getHeader("X-Telegram-Init-Data")
            ?: request.getHeader("x-telegram-init-data")
            ?: ""
        val initUser = TelegramAuth.validateInitData(initData, properties.botToken)
        if (initUser != null) {
            val seller = catalogService.getSellerByTgId(initUser.id)
            if (seller == null) {
                writeJsonError(response, HttpStatus.UNAUTHORIZED, "seller not found, run /start in bot first")
                return false
            }
            request.setAttribute(HttpSessionAttributes.INIT_USER, initUser)
            request.setAttribute(HttpSessionAttributes.SELLER_ID, seller.id!!)
            request.setAttribute(HttpSessionAttributes.TG_USER_ID, initUser.id)
            return true
        }

        val handoffToken = request.getHeader("X-Login-Handoff")
            ?: request.getHeader("x-login-handoff")
            ?: request.getParameter("handoff")
            ?: ""
        val payload = loginHandoff.resolve(handoffToken)
        if (payload != null) {
            request.setAttribute(HttpSessionAttributes.SELLER_ID, payload.sellerId)
            request.setAttribute(HttpSessionAttributes.TG_USER_ID, payload.tgUserId)
            return true
        }

        writeJsonError(
            response,
            HttpStatus.UNAUTHORIZED,
            "open from Telegram or use the Add worker button in the dashboard",
        )
        return false
    }

    private fun writeJsonError(response: HttpServletResponse, status: HttpStatus, message: String) {
        response.status = status.value()
        response.contentType = MediaType.APPLICATION_JSON_VALUE
        response.writer.write(objectMapper.writeValueAsString(mapOf("error" to message)))
    }
}

fun HttpServletRequest.sellerId(): Long =
    getAttribute(HttpSessionAttributes.SELLER_ID) as Long

fun HttpServletRequest.tgUserId(): Long =
    getAttribute(HttpSessionAttributes.TG_USER_ID) as Long

fun HttpServletRequest.initUser(): TelegramUser? =
    getAttribute(HttpSessionAttributes.INIT_USER) as? TelegramUser

fun loginActorKey(request: HttpServletRequest): String {
    request.initUser()?.id?.let { return it.toString() }
    val tgUserId = request.getAttribute(HttpSessionAttributes.TG_USER_ID) as? Long
    if (tgUserId != null) return tgUserId.toString()
    return "seller:${request.sellerId()}"
}
