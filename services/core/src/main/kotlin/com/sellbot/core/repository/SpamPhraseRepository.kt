package com.sellbot.core.repository

import com.sellbot.core.domain.SpamPhraseEntity
import org.springframework.data.jpa.repository.JpaRepository

interface SpamPhraseRepository : JpaRepository<SpamPhraseEntity, Long> {
    fun findBySellerId(sellerId: Long): List<SpamPhraseEntity>

    fun existsBySellerIdAndPhrase(sellerId: Long, phrase: String): Boolean
}
