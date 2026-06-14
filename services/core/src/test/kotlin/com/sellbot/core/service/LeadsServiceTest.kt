package com.sellbot.core.service

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.LeadRepository
import com.sellbot.core.repository.ProductRepository
import com.sellbot.core.repository.WorkerRepository
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.junit.jupiter.MockitoExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.eq
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import java.math.BigDecimal
import java.time.Instant

@ExtendWith(MockitoExtension::class)
class LeadsServiceTest {

    @Mock
    lateinit var leadRepository: LeadRepository

    @Mock
    lateinit var catalogService: CatalogService

    @Mock
    lateinit var productRepository: ProductRepository

    @Mock
    lateinit var workerRepository: WorkerRepository

    @Mock
    lateinit var notificationService: NotificationService

    @Mock
    lateinit var spamLearningService: SpamLearningService

    @InjectMocks
    lateinit var leadsService: LeadsService

    private val seller = SellerEntity(id = 1L, tgUserId = 100L)

    @Test
    fun `createLead persists entity`() {
        whenever(catalogService.getSeller(1L)).thenReturn(seller)
        whenever(leadRepository.save(any<LeadEntity>())).thenAnswer { invocation ->
            val lead = invocation.getArgument<LeadEntity>(0)
            lead.id = 42L
            lead
        }

        val lead = leadsService.createLead(
            CreateLeadInput(
                sellerId = 1L,
                productId = null,
                workerId = null,
                chatId = -100123L,
                messageId = 99L,
                authorId = 555L,
                authorUsername = "buyer",
                rawText = "куплю айфон",
                matchedKeywords = listOf("айфон"),
                productScore = BigDecimal("0.9"),
                intentScore = BigDecimal("0.9"),
                score = BigDecimal("0.9"),
                level = "confirmed",
            ),
        )

        assertEquals(42L, lead.id)
        assertEquals("куплю айфон", lead.rawText)
        verify(leadRepository).save(any())
        verify(notificationService).enqueueLeadNotification(any(), eq(seller), any(), any())
    }

    @Test
    fun `updateStatus throws when lead not found`() {
        whenever(leadRepository.findByIdAndSellerId(1L, 1L)).thenReturn(null)

        assertThrows(IllegalArgumentException::class.java) {
            leadsService.updateStatus(1L, 1L, "contacted")
        }
    }

    @Test
    fun `listLeads paginates results`() {
        val leads = (1..5).map { i ->
            LeadEntity(
                id = i.toLong(),
                seller = seller,
                chatId = 1L,
                messageId = i.toLong(),
                authorId = 1L,
                rawText = "text $i",
                level = "confirmed",
                createdAt = Instant.now(),
            )
        }
        whenever(leadRepository.findBySellerIdOrderByCreatedAtDesc(1L)).thenReturn(leads)

        val (slice, total) = leadsService.listLeads(1L, null, limit = 2, offset = 1)

        assertEquals(2, slice.size)
        assertEquals(5, total)
        assertEquals(2L, slice[0].id)
        assertEquals(3L, slice[1].id)
    }

    @Test
    fun `getStats aggregates counts`() {
        whenever(leadRepository.countBySellerSince(eq(1L), any())).thenReturn(10L)
        whenever(leadRepository.countBySellerStatusSince(eq(1L), eq("new"), any())).thenReturn(4L)
        whenever(leadRepository.countBySellerStatusSince(eq(1L), eq("contacted"), any())).thenReturn(3L)
        whenever(leadRepository.countBySellerStatusSince(eq(1L), eq("closed"), any())).thenReturn(2L)
        whenever(leadRepository.countBySellerStatusSince(eq(1L), eq("spam"), any())).thenReturn(1L)

        val stats = leadsService.getStats(1L, days = 30)

        assertEquals(10, stats.total)
        assertEquals(4, stats.newCount)
        assertEquals(3, stats.contacted)
        assertEquals(2, stats.closed)
        assertEquals(1, stats.spam)
    }
}
