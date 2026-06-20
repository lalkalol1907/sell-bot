package com.sellbot.core.service

import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.domain.SellerMemberEntity
import com.sellbot.core.repository.SellerMemberRepository
import com.sellbot.core.repository.SellerRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.Instant

data class SellerAccess(
    val seller: SellerEntity,
    val isOwner: Boolean,
)

@Service
class TeamService(
    private val sellerRepository: SellerRepository,
    private val memberRepository: SellerMemberRepository,
) {
    fun resolveDashboardAccess(tgUserId: Long): SellerAccess? {
        sellerRepository.findByTgUserId(tgUserId).orElse(null)?.let {
            return SellerAccess(it, isOwner = true)
        }
        val member = memberRepository.findByTgUserIdAndStatus(tgUserId, SellerMemberEntity.STATUS_ACTIVE)
            ?: return null
        return SellerAccess(member.seller, isOwner = false)
    }

    @Transactional
    fun resolveBotSession(tgUserId: Long, username: String?, fullName: String?): SellerAccess {
        sellerRepository.findByTgUserId(tgUserId).orElse(null)?.let {
            return SellerAccess(it, isOwner = true)
        }

        memberRepository.findByTgUserIdAndStatus(tgUserId, SellerMemberEntity.STATUS_ACTIVE)?.let { member ->
            refreshMemberProfile(member, username, fullName)
            return SellerAccess(member.seller, isOwner = false)
        }

        val normalizedUsername = normalizeUsername(username)
        if (normalizedUsername.isNotBlank()) {
            val pending = memberRepository
                .findByUsernameIgnoreCaseAndStatus(normalizedUsername, SellerMemberEntity.STATUS_PENDING)
                .firstOrNull()
            if (pending != null) {
                activateMember(pending, tgUserId, fullName)
                return SellerAccess(pending.seller, isOwner = false)
            }
        }

        val seller = sellerRepository.save(
            SellerEntity(
                tgUserId = tgUserId,
                username = username?.takeIf { it.isNotBlank() },
                fullName = fullName?.takeIf { it.isNotBlank() },
            )
        )
        return SellerAccess(seller, isOwner = true)
    }

    fun listMembers(sellerId: Long): List<SellerMemberEntity> =
        memberRepository.findBySellerIdOrderByCreatedAtDesc(sellerId)

    fun listNotifyTgUserIds(seller: SellerEntity): List<Long> {
        val ids = linkedSetOf(seller.tgUserId)
        memberRepository.findBySellerIdAndStatus(seller.id!!, SellerMemberEntity.STATUS_ACTIVE)
            .mapNotNull { it.tgUserId }
            .forEach { ids.add(it) }
        return ids.toList()
    }

    fun isOwner(sellerId: Long, tgUserId: Long): Boolean {
        val seller = sellerRepository.findById(sellerId).orElse(null) ?: return false
        return seller.tgUserId == tgUserId
    }

    @Transactional
    fun inviteMember(sellerId: Long, ownerTgUserId: Long, username: String): SellerMemberEntity {
        require(isOwner(sellerId, ownerTgUserId)) { "Only the account owner can invite team members" }

        val normalized = normalizeUsername(username)
        require(normalized.isNotBlank()) { "Username is required" }

        val seller = sellerRepository.findById(sellerId).orElseThrow { IllegalArgumentException("Seller not found") }
        if (seller.username?.equals(normalized, ignoreCase = true) == true) {
            throw IllegalArgumentException("Cannot invite the account owner")
        }

        memberRepository.findBySellerIdAndUsernameIgnoreCase(sellerId, normalized)?.let {
            throw IllegalArgumentException("Member already invited")
        }

        return memberRepository.save(
            SellerMemberEntity(
                seller = seller,
                username = normalized,
                status = SellerMemberEntity.STATUS_PENDING,
            )
        )
    }

    @Transactional
    fun removeMember(sellerId: Long, ownerTgUserId: Long, memberId: Long): Boolean {
        require(isOwner(sellerId, ownerTgUserId)) { "Only the account owner can remove team members" }
        val member = memberRepository.findBySellerIdAndId(sellerId, memberId) ?: return false
        memberRepository.delete(member)
        return true
    }

    private fun activateMember(member: SellerMemberEntity, tgUserId: Long, fullName: String?) {
        member.tgUserId = tgUserId
        member.status = SellerMemberEntity.STATUS_ACTIVE
        member.joinedAt = Instant.now()
        if (!fullName.isNullOrBlank()) {
            member.fullName = fullName
        }
        memberRepository.save(member)
    }

    private fun refreshMemberProfile(member: SellerMemberEntity, username: String?, fullName: String?) {
        var changed = false
        val normalized = normalizeUsername(username)
        if (normalized.isNotBlank() && !member.username.equals(normalized, ignoreCase = true)) {
            member.username = normalized
            changed = true
        }
        if (!fullName.isNullOrBlank() && member.fullName != fullName) {
            member.fullName = fullName
            changed = true
        }
        if (changed) {
            memberRepository.save(member)
        }
    }

    private fun normalizeUsername(username: String?): String =
        username?.trim()?.removePrefix("@")?.lowercase().orEmpty()
}
