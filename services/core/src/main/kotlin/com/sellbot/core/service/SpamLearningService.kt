package com.sellbot.core.service

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.domain.SpamPhraseEntity
import com.sellbot.core.repository.SpamPhraseRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
class SpamLearningService(
    private val spamPhraseRepository: SpamPhraseRepository,
) {
    fun listPhrases(sellerId: Long): List<String> =
        spamPhraseRepository.findBySellerId(sellerId).map { it.phrase }

    @Transactional
    fun learnFromLead(lead: LeadEntity) {
        val seller = lead.seller
        val phrases = extractPhrases(lead.rawText)
        for (phrase in phrases) {
            if (spamPhraseRepository.existsBySellerIdAndPhrase(seller.id!!, phrase)) {
                continue
            }
            spamPhraseRepository.save(
                SpamPhraseEntity(
                    seller = seller,
                    phrase = phrase,
                    sourceLeadId = lead.id,
                )
            )
        }
    }

    private fun extractPhrases(rawText: String): List<String> {
        val normalized = normalizeText(rawText)
        if (normalized.isBlank()) {
            return emptyList()
        }
        val out = linkedSetOf<String>()
        if (normalized.length >= 4) {
            out.add(normalized)
        }
        normalized.split(Regex("\\s+"))
            .map { it.trim() }
            .filter { it.length >= 4 }
            .forEach { out.add(it) }
        return out.toList()
    }

    private fun normalizeText(text: String): String {
        val lower = text.lowercase().trim()
        return lower.replace(Regex("[^\\p{L}\\p{N}\\s]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
    }
}
