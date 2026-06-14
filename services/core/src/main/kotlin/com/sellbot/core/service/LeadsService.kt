package com.sellbot.core.service

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.repository.LeadRepository
import com.sellbot.core.repository.ProductRepository
import com.sellbot.core.repository.WorkerRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.math.BigDecimal
import java.time.Instant
import java.time.temporal.ChronoUnit

data class CreateLeadInput(
    val sellerId: Long,
    val productId: Long?,
    val workerId: Long?,
    val chatId: Long,
    val messageId: Long,
    val authorId: Long,
    val authorUsername: String?,
    val rawText: String,
    val matchedKeywords: List<String>,
    val productScore: BigDecimal,
    val intentScore: BigDecimal,
    val score: BigDecimal,
    val level: String,
)

data class LeadStatsResult(
    val total: Int,
    val newCount: Int,
    val contacted: Int,
    val closed: Int,
    val spam: Int,
)

@Service
class LeadsService(
    private val leadRepository: LeadRepository,
    private val catalogService: CatalogService,
    private val productRepository: ProductRepository,
    private val workerRepository: WorkerRepository,
) {
    @Transactional
    fun createLead(input: CreateLeadInput): LeadEntity {
        val seller = catalogService.getSeller(input.sellerId)
        val product = input.productId?.let { productRepository.findById(it).orElse(null) }
        val worker = input.workerId?.let { workerRepository.findById(it).orElse(null) }

        return leadRepository.save(
            LeadEntity(
                seller = seller,
                product = product,
                worker = worker,
                chatId = input.chatId,
                messageId = input.messageId,
                authorId = input.authorId,
                authorUsername = input.authorUsername,
                rawText = input.rawText,
                matchedKeywords = input.matchedKeywords.toTypedArray(),
                productScore = input.productScore,
                intentScore = input.intentScore,
                score = input.score,
                level = input.level,
            )
        )
    }

    @Transactional
    fun updateStatus(id: Long, sellerId: Long, status: String): LeadEntity {
        val lead = leadRepository.findByIdAndSellerId(id, sellerId)
            ?: throw IllegalArgumentException("Lead not found: $id")
        lead.status = status
        return leadRepository.save(lead)
    }

    fun listLeads(sellerId: Long, status: String?, limit: Int, offset: Int): Pair<List<LeadEntity>, Int> {
        val all = if (status.isNullOrBlank()) {
            leadRepository.findBySellerIdOrderByCreatedAtDesc(sellerId)
        } else {
            leadRepository.findBySellerIdAndStatusOrderByCreatedAtDesc(sellerId, status)
        }
        val slice = all.drop(offset).take(limit)
        return slice to all.size
    }

    fun getStats(sellerId: Long, days: Int): LeadStatsResult {
        val since = Instant.now().minus(days.toLong(), ChronoUnit.DAYS)
        return LeadStatsResult(
            total = leadRepository.countBySellerSince(sellerId, since).toInt(),
            newCount = leadRepository.countBySellerStatusSince(sellerId, "new", since).toInt(),
            contacted = leadRepository.countBySellerStatusSince(sellerId, "contacted", since).toInt(),
            closed = leadRepository.countBySellerStatusSince(sellerId, "closed", since).toInt(),
            spam = leadRepository.countBySellerStatusSince(sellerId, "spam", since).toInt(),
        )
    }
}
