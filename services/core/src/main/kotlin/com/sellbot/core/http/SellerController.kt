package com.sellbot.core.http

import com.sellbot.core.http.dto.toDto
import com.sellbot.core.http.redis.LoginHandoff
import com.sellbot.core.http.redis.LoginHandoff.Companion.buildLoginHandoffUrl
import com.sellbot.core.nats.NatsClient
import com.sellbot.core.service.CatalogService
import com.sellbot.core.service.LeadsService
import com.sellbot.core.service.WorkersService
import com.sellbot.core.service.WhitelistEntry
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.DeleteMapping
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PatchMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import java.math.BigDecimal

@RestController
@RequestMapping("/api/v1/seller")
class SellerController(
    private val catalogService: CatalogService,
    private val leadsService: LeadsService,
    private val workersService: WorkersService,
    private val natsClient: NatsClient,
) {

    @GetMapping("/stats")
    fun stats(
        request: jakarta.servlet.http.HttpServletRequest,
        @RequestParam(defaultValue = "30") days: Int,
    ) = leadsService.getStats(request.sellerId(), days).toDto()

    @GetMapping("/products")
    fun listProducts(request: jakarta.servlet.http.HttpServletRequest) =
        mapOf("products" to catalogService.listProducts(request.sellerId(), activeOnly = false).map { it.toDto() })

    @PostMapping("/products")
    fun createProduct(
        request: jakarta.servlet.http.HttpServletRequest,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val product = body["product"] as? Map<*, *> ?: emptyMap<String, Any?>()
        return try {
            val created = catalogService.createProduct(
                sellerId = request.sellerId(),
                title = product["title"]?.toString() ?: "",
                price = BigDecimal(product["price"]?.toString()?.ifBlank { "0" } ?: "0"),
                currency = product["currency"]?.toString()?.ifBlank { "RUB" } ?: "RUB",
                keywords = (product["keywords"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            )
            ResponseEntity.status(HttpStatus.CREATED).body(created.toDto())
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid product")))
        }
    }

    @PatchMapping("/products/{id}")
    fun updateProduct(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val product = body["product"] as? Map<*, *> ?: emptyMap<String, Any?>()
        return try {
            val updated = catalogService.updateProduct(
                id = id,
                sellerId = request.sellerId(),
                title = product["title"]?.toString() ?: "",
                price = BigDecimal(product["price"]?.toString()?.ifBlank { "0" } ?: "0"),
                currency = product["currency"]?.toString()?.ifBlank { "RUB" } ?: "RUB",
                keywords = (product["keywords"] as? List<*>)?.map { it.toString() } ?: emptyList(),
                isActive = product["is_active"]?.let { it as? Boolean } ?: true,
            )
            ResponseEntity.ok(updated.toDto())
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid product")))
        }
    }

    @DeleteMapping("/products/{id}")
    fun deleteProduct(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
    ) = mapOf("success" to catalogService.deleteProduct(id, request.sellerId()))

    @GetMapping("/leads")
    fun listLeads(
        request: jakarta.servlet.http.HttpServletRequest,
        @RequestParam(defaultValue = "") status: String,
        @RequestParam(defaultValue = "50") limit: Int,
        @RequestParam(defaultValue = "0") offset: Int,
    ): Map<String, Any> {
        val (leads, total) = leadsService.listLeads(request.sellerId(), status, limit, offset)
        return mapOf(
            "leads" to leads.map { it.toDto() },
            "total" to total,
        )
    }

    @PatchMapping("/leads/{id}")
    fun updateLead(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val lead = body["lead"] as? Map<*, *>
        val status = lead?.get("status")?.toString() ?: ""
        return try {
            ResponseEntity.ok(leadsService.updateStatus(id, request.sellerId(), status).toDto())
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid lead")))
        }
    }

    @GetMapping("/workers")
    fun listWorkers(request: jakarta.servlet.http.HttpServletRequest) =
        mapOf("workers" to workersService.listWorkers(request.sellerId()).map { it.toDto() })

    @PatchMapping("/workers/{id}/status")
    fun updateWorkerStatus(
        @PathVariable id: Long,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val worker = body["worker"] as? Map<*, *>
        val status = worker?.get("status")?.toString() ?: ""
        return try {
            ResponseEntity.ok(workersService.updateStatus(id, status).toDto())
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid worker")))
        }
    }

    @GetMapping("/workers/{id}/chats")
    fun listChats(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
    ): ResponseEntity<Any> = try {
        ResponseEntity.ok(
            mapOf("chats" to workersService.listChats(id, request.sellerId()).map { it.toDto() }),
        )
    } catch (e: Exception) {
        ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(mapOf("error" to (e.message ?: "worker not found")))
    }

    @PatchMapping("/workers/{id}/chats/whitelist")
    fun setChatWhitelist(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val entriesRaw = body["entries"] as? List<*> ?: emptyList<Any>()
        val entries = entriesRaw.mapNotNull { item ->
            val map = item as? Map<*, *> ?: return@mapNotNull null
            val chatId = (map["chat_id"] as? Number)?.toLong() ?: return@mapNotNull null
            val isActive = map["is_active"] as? Boolean ?: return@mapNotNull null
            WhitelistEntry(chatId = chatId, isActive = isActive)
        }
        return try {
            val updated = workersService.setChatWhitelist(id, request.sellerId(), entries)
            ResponseEntity.ok(mapOf("updated" to updated))
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid chat whitelist")))
        }
    }

    @PostMapping("/workers/{id}/chats/sync")
    fun syncChats(
        request: jakarta.servlet.http.HttpServletRequest,
        @PathVariable id: Long,
    ): ResponseEntity<Any> {
        try {
            workersService.listChats(id, request.sellerId())
        } catch (e: Exception) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(mapOf("error" to (e.message ?: "worker not found")))
        }

        return try {
            natsClient.publishDirect(
                "worker.sync_chats",
                """{"worker_id":$id}""".toByteArray(),
            )
            ResponseEntity.status(HttpStatus.ACCEPTED).body(mapOf("ok" to true))
        } catch (e: Exception) {
            ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(mapOf("error" to (e.message ?: "sync request failed")))
        }
    }

    @PatchMapping("/settings")
    fun updateSettings(
        request: jakarta.servlet.http.HttpServletRequest,
        @RequestBody body: Map<String, Any?>,
    ): ResponseEntity<Any> {
        val settings = body["settings"] as? Map<*, *>
        val sensitivity = settings?.get("sensitivity")?.toString() ?: ""
        return try {
            val seller = catalogService.updateSellerSensitivity(request.sellerId(), sensitivity)
            ResponseEntity.ok(mapOf("id" to seller.id, "sensitivity" to seller.sensitivity))
        } catch (e: Exception) {
            ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "invalid settings")))
        }
    }
}

@RestController
@RequestMapping("/api/v1/login")
class LoginHandoffController(
    private val properties: SellbotHttpProperties,
    private val loginHandoff: LoginHandoff,
) {
    @PostMapping("/handoff")
    fun handoff(request: jakarta.servlet.http.HttpServletRequest): Map<String, String> {
        val token = loginHandoff.create(request.sellerId(), request.tgUserId())
        val url = buildLoginHandoffUrl(properties.loginWebUrl, token)
        return mapOf("token" to token, "url" to url)
    }
}
