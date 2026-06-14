package com.sellbot.core.service

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.SpamPhraseRepository
import org.junit.jupiter.api.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.atLeast
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class SpamLearningServiceTest {
    private val spamPhraseRepository = mock<SpamPhraseRepository>()
    private val service = SpamLearningService(spamPhraseRepository)

    @Test
    fun `learnFromLead stores normalized phrases`() {
        val seller = SellerEntity(id = 1L, tgUserId = 100L)
        val lead = LeadEntity(
            seller = seller,
            chatId = 1,
            messageId = 1,
            authorId = 2,
            rawText = "Спам курс по заработку",
            level = "probable",
        ).apply { id = 10L }

        whenever(spamPhraseRepository.existsBySellerIdAndPhrase(any(), any())).thenReturn(false)

        service.learnFromLead(lead)

        verify(spamPhraseRepository, atLeast(1)).save(any())
    }

    @Test
    fun `learnFromLead skips duplicates`() {
        val seller = SellerEntity(id = 1L, tgUserId = 100L)
        val lead = LeadEntity(
            seller = seller,
            chatId = 1,
            messageId = 1,
            authorId = 2,
            rawText = "курс по заработку",
            level = "probable",
        )

        whenever(spamPhraseRepository.existsBySellerIdAndPhrase(eq(1L), any())).thenReturn(true)

        service.learnFromLead(lead)

        verify(spamPhraseRepository, never()).save(any())
    }
}
