package com.sellbot.core.nats

import com.sellbot.core.service.NotificationService
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component

@Component
class NotificationDispatcher(
    private val notificationService: NotificationService,
    private val natsClient: NatsClient,
    @Value("\${sellbot.notifications.batch-size:50}") private val batchSize: Int,
    @Value("\${sellbot.notifications.stale-minutes:5}") private val staleMinutes: Long,
) {
    private val log = LoggerFactory.getLogger(NotificationDispatcher::class.java)

    @Scheduled(fixedDelayString = "\${sellbot.notifications.dispatch-interval-ms:5000}")
    fun dispatchPending() {
        val recovered = notificationService.recoverStaleProcessing(staleMinutes)
        if (recovered > 0) {
            log.info("recovered {} stale processing notifications", recovered)
        }

        val batch = notificationService.claimPendingBatch(batchSize)
        if (batch.isEmpty()) {
            return
        }

        for (notification in batch) {
            try {
                natsClient.publish("lead.created", notification.payload.toByteArray(Charsets.UTF_8))
                notificationService.markSent(notification)
                log.info("dispatched lead notification id={} lead_id={}", notification.id, notification.lead.id)
            } catch (e: Exception) {
                log.warn("failed to dispatch notification id={}: {}", notification.id, e.message)
                notificationService.markFailed(notification, e.message ?: "unknown error")
            }
        }
    }
}
