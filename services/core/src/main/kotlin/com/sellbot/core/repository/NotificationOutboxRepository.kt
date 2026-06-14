package com.sellbot.core.repository

import com.sellbot.core.domain.NotificationEntity
import jakarta.persistence.EntityManager
import org.springframework.stereotype.Repository
import org.springframework.transaction.annotation.Transactional

@Repository
class NotificationOutboxRepository(
    private val entityManager: EntityManager,
    private val notificationRepository: NotificationRepository,
) {
    @Transactional
    fun claimPendingBatch(limit: Int): List<NotificationEntity> {
        @Suppress("UNCHECKED_CAST")
        val ids = entityManager.createNativeQuery(
            """
            SELECT id FROM notifications
            WHERE delivery_status = 'pending'
            ORDER BY created_at ASC
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
            """.trimIndent(),
        )
            .setParameter("limit", limit)
            .resultList as List<Number>

        if (ids.isEmpty()) {
            return emptyList()
        }

        val longIds = ids.map { it.toLong() }
        entityManager.createNativeQuery(
            """
            UPDATE notifications
            SET delivery_status = 'processing', claimed_at = NOW()
            WHERE id IN (:ids) AND delivery_status = 'pending'
            """.trimIndent(),
        )
            .setParameter("ids", longIds)
            .executeUpdate()

        entityManager.flush()
        entityManager.clear()
        return notificationRepository.findAllById(longIds)
            .filter { it.deliveryStatus == "processing" }
            .sortedBy { it.createdAt }
    }

    @Transactional
    fun recoverStaleProcessing(staleMinutes: Long): Int =
        entityManager.createNativeQuery(
            """
            UPDATE notifications
            SET delivery_status = 'pending', claimed_at = NULL
            WHERE delivery_status = 'processing'
              AND claimed_at IS NOT NULL
              AND claimed_at < NOW() - (:minutes * INTERVAL '1 minute')
            """.trimIndent(),
        )
            .setParameter("minutes", staleMinutes)
            .executeUpdate()
}
