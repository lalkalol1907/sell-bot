package com.sellbot.core.service

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.NotificationEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.NotificationOutboxRepository
import com.sellbot.core.repository.NotificationRepository
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.mockito.Mock
import org.mockito.junit.jupiter.MockitoExtension
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@ExtendWith(MockitoExtension::class)
class NotificationServiceTest {

    @Mock
    lateinit var notificationRepository: NotificationRepository

    @Mock
    lateinit var notificationOutboxRepository: NotificationOutboxRepository

    private val objectMapper: ObjectMapper = jacksonObjectMapper()
    private lateinit var notificationService: NotificationService

    @BeforeEach
    fun setUp() {
        notificationService = NotificationService(
            notificationRepository,
            notificationOutboxRepository,
            objectMapper,
        )
    }

    private fun sampleNotification(): NotificationEntity {
        val seller = SellerEntity(id = 1L, tgUserId = 100L)
        val lead = LeadEntity(
            seller = seller,
            chatId = 1L,
            messageId = 1L,
            authorId = 2L,
            rawText = "test",
            level = "confirmed",
        ).apply { id = 10L }
        return NotificationEntity(
            id = 5L,
            lead = lead,
            seller = seller,
            payload = "{}",
            deliveryStatus = "processing",
            attempts = 0,
        )
    }

    @Test
    fun `markFailed returns notification to pending before max attempts`() {
        val notification = sampleNotification()
        whenever(notificationRepository.save(notification)).thenAnswer { it.arguments[0] }

        notificationService.markFailed(notification, "nats down")

        assertEquals("pending", notification.deliveryStatus)
        assertEquals(1, notification.attempts)
        assertEquals(null, notification.claimedAt)
        verify(notificationRepository).save(notification)
    }

    @Test
    fun `markFailed marks failed after max attempts`() {
        val notification = sampleNotification().apply { attempts = 9 }
        whenever(notificationRepository.save(notification)).thenAnswer { it.arguments[0] }

        notificationService.markFailed(notification, "nats down")

        assertEquals("failed", notification.deliveryStatus)
        assertEquals(10, notification.attempts)
    }
}
