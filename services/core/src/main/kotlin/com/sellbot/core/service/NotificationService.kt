package com.sellbot.core.service

import com.fasterxml.jackson.databind.ObjectMapper
import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.NotificationEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.NotificationOutboxRepository
import com.sellbot.core.repository.NotificationRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
class NotificationService(
    private val notificationRepository: NotificationRepository,
    private val notificationOutboxRepository: NotificationOutboxRepository,
    private val objectMapper: ObjectMapper,
) {
    @Transactional
    fun enqueueLeadNotification(
        lead: LeadEntity,
        seller: SellerEntity,
        productTitle: String,
        chatTitle: String,
    ): NotificationEntity {
        val payload = mapOf(
            "lead_id" to lead.id,
            "seller_id" to seller.id,
            "tg_user_id" to seller.tgUserId,
            "product_id" to (lead.product?.id ?: 0),
            "product_title" to productTitle,
            "worker_id" to (lead.worker?.id ?: 0),
            "chat_id" to lead.chatId,
            "message_id" to lead.messageId,
            "author_id" to lead.authorId,
            "author_username" to (lead.authorUsername ?: ""),
            "chat_title" to chatTitle,
            "raw_text" to lead.rawText,
            "matched_keywords" to lead.matchedKeywords.toList(),
            "product_score" to lead.productScore.toDouble(),
            "intent_score" to lead.intentScore.toDouble(),
            "score" to lead.score.toDouble(),
            "level" to lead.level,
        )
        return notificationRepository.save(
            NotificationEntity(
                lead = lead,
                seller = seller,
                payload = objectMapper.writeValueAsString(payload),
                deliveryStatus = "pending",
            )
        )
    }

    fun claimPendingBatch(limit: Int): List<NotificationEntity> =
        notificationOutboxRepository.claimPendingBatch(limit)

    fun recoverStaleProcessing(staleMinutes: Long): Int =
        notificationOutboxRepository.recoverStaleProcessing(staleMinutes)

    @Transactional
    fun markSent(notification: NotificationEntity) {
        notification.deliveryStatus = "sent"
        notification.sentAt = java.time.Instant.now()
        notification.claimedAt = null
        notification.lastError = null
        notificationRepository.save(notification)
    }

    @Transactional
    fun markFailed(notification: NotificationEntity, error: String) {
        notification.attempts += 1
        notification.lastError = error.take(500)
        notification.claimedAt = null
        if (notification.attempts >= 10) {
            notification.deliveryStatus = "failed"
        } else {
            notification.deliveryStatus = "pending"
        }
        notificationRepository.save(notification)
    }
}
