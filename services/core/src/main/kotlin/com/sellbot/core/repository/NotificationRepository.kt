package com.sellbot.core.repository

import com.sellbot.core.domain.NotificationEntity
import org.springframework.data.jpa.repository.JpaRepository

interface NotificationRepository : JpaRepository<NotificationEntity, Long> {
    fun findTop50ByDeliveryStatusOrderByCreatedAtAsc(status: String): List<NotificationEntity>
}
