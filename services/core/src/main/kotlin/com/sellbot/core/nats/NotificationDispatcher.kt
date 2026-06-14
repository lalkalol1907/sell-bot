package com.sellbot.core.nats

import com.sellbot.core.service.NotificationService
import org.slf4j.LoggerFactory
import org.springframework.scheduling.annotation.EnableScheduling
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Component

@Component
class NotificationDispatcher(
    private val notificationService: NotificationService,
    private val natsClient: NatsClient,
) {
    private val log = LoggerFactory.getLogger(NotificationDispatcher::class.java)

    @Scheduled(fixedDelayString = "\${sellbot.notifications.dispatch-interval-ms:5000}")
    fun dispatchPending() {
        val pending = notificationService.listPending()
        if (pending.isEmpty()) {
            return
        }
        for (notification in pending) {
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
