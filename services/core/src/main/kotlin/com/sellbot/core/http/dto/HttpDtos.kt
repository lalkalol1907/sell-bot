package com.sellbot.core.http.dto

import com.fasterxml.jackson.databind.PropertyNamingStrategies
import com.fasterxml.jackson.databind.annotation.JsonNaming
import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.MonitoredChatEntity
import com.sellbot.core.domain.ProductEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.domain.WorkerEntity
import com.sellbot.core.http.grpc.LoginStep
import com.sellbot.core.service.LeadStatsResult

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class SellerDto(
    val id: Long,
    val tgUserId: Long,
    val username: String,
    val fullName: String,
    val sensitivity: String,
    val plan: String,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class ProductDto(
    val id: Long,
    val sellerId: Long,
    val title: String,
    val price: String,
    val currency: String,
    val keywords: List<String>,
    val isActive: Boolean,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class LeadDto(
    val id: Long,
    val sellerId: Long,
    val productId: Long,
    val workerId: Long,
    val chatId: Long,
    val messageId: Long,
    val authorId: Long,
    val authorUsername: String,
    val rawText: String,
    val matchedKeywords: List<String>,
    val productScore: Double,
    val intentScore: Double,
    val score: Double,
    val level: String,
    val status: String,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class WorkerDto(
    val id: Long,
    val ownerSellerId: Long,
    val tgAccountId: Long,
    val phone: String,
    val proxy: String,
    val status: String,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class MonitoredChatDto(
    val id: Long,
    val workerId: Long,
    val chatId: Long,
    val title: String,
    val type: String,
    val isActive: Boolean,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class LeadStatsDto(
    val total: Int,
    val newCount: Int,
    val contacted: Int,
    val closed: Int,
    val spam: Int,
)

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy::class)
data class LoginStepDto(
    val loginId: String,
    val status: String,
    val message: String,
    val workerId: Long,
    val qrUrl: String,
    val qrExpiresAt: Long,
)

fun SellerEntity.toDto() = SellerDto(
    id = id!!,
    tgUserId = tgUserId,
    username = username ?: "",
    fullName = fullName ?: "",
    sensitivity = sensitivity,
    plan = plan,
)

fun ProductEntity.toDto() = ProductDto(
    id = id!!,
    sellerId = seller.id!!,
    title = title,
    price = price.toPlainString(),
    currency = currency,
    keywords = keywords.toList(),
    isActive = isActive,
)

fun LeadEntity.toDto() = LeadDto(
    id = id!!,
    sellerId = seller.id!!,
    productId = product?.id ?: 0,
    workerId = worker?.id ?: 0,
    chatId = chatId,
    messageId = messageId,
    authorId = authorId,
    authorUsername = authorUsername ?: "",
    rawText = rawText,
    matchedKeywords = matchedKeywords.toList(),
    productScore = productScore.toDouble(),
    intentScore = intentScore.toDouble(),
    score = score.toDouble(),
    level = level,
    status = status,
)

fun WorkerEntity.toDto() = WorkerDto(
    id = id!!,
    ownerSellerId = ownerSeller.id!!,
    tgAccountId = tgAccountId ?: 0,
    phone = phone ?: "",
    proxy = proxy ?: "",
    status = status,
)

fun MonitoredChatEntity.toDto() = MonitoredChatDto(
    id = id!!,
    workerId = worker.id!!,
    chatId = chatId,
    title = title ?: "",
    type = type ?: "",
    isActive = isActive,
)

fun LeadStatsResult.toDto() = LeadStatsDto(
    total = total,
    newCount = newCount,
    contacted = contacted,
    closed = closed,
    spam = spam,
)

fun LoginStep.toDto() = LoginStepDto(
    loginId = loginId,
    status = status,
    message = message,
    workerId = workerId,
    qrUrl = qrUrl,
    qrExpiresAt = qrExpiresAt,
)
