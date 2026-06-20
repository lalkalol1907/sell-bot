package com.sellbot.core.service

import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.domain.SellerMemberEntity
import com.sellbot.core.repository.SellerMemberRepository
import com.sellbot.core.repository.SellerRepository
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.junit.jupiter.MockitoExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import java.util.Optional

@ExtendWith(MockitoExtension::class)
class TeamServiceTest {

    @Mock
    lateinit var sellerRepository: SellerRepository

    @Mock
    lateinit var memberRepository: SellerMemberRepository

    @InjectMocks
    lateinit var teamService: TeamService

    private fun seller(id: Long = 1L, tgUserId: Long = 100L) = SellerEntity(
        id = id,
        tgUserId = tgUserId,
        username = "owner",
        fullName = "Owner",
    )

    @Test
    fun `resolveDashboardAccess returns owner`() {
        whenever(sellerRepository.findByTgUserId(100L)).thenReturn(Optional.of(seller()))

        val access = teamService.resolveDashboardAccess(100L)

        assertTrue(access!!.isOwner)
        assertEquals(1L, access.seller.id)
    }

    @Test
    fun `resolveDashboardAccess returns active member`() {
        whenever(sellerRepository.findByTgUserId(200L)).thenReturn(Optional.empty())
        val member = SellerMemberEntity(
            id = 5L,
            seller = seller(),
            tgUserId = 200L,
            username = "staff",
            status = SellerMemberEntity.STATUS_ACTIVE,
        )
        whenever(memberRepository.findByTgUserIdAndStatus(200L, SellerMemberEntity.STATUS_ACTIVE))
            .thenReturn(member)

        val access = teamService.resolveDashboardAccess(200L)

        assertFalse(access!!.isOwner)
        assertEquals(1L, access.seller.id)
    }

    @Test
    fun `resolveBotSession activates pending invite`() {
        whenever(sellerRepository.findByTgUserId(200L)).thenReturn(Optional.empty())
        whenever(memberRepository.findByTgUserIdAndStatus(200L, SellerMemberEntity.STATUS_ACTIVE))
            .thenReturn(null)
        val pending = SellerMemberEntity(
            id = 7L,
            seller = seller(),
            username = "staff",
            status = SellerMemberEntity.STATUS_PENDING,
        )
        whenever(
            memberRepository.findByUsernameIgnoreCaseAndStatus("staff", SellerMemberEntity.STATUS_PENDING),
        ).thenReturn(listOf(pending))
        whenever(memberRepository.save(any())).thenAnswer { it.arguments[0] as SellerMemberEntity }

        val access = teamService.resolveBotSession(200L, "staff", "Staff User")

        assertFalse(access.isOwner)
        assertEquals(SellerMemberEntity.STATUS_ACTIVE, pending.status)
        assertEquals(200L, pending.tgUserId)
        verify(sellerRepository, never()).save(any())
    }

    @Test
    fun `listNotifyTgUserIds includes owner and active members`() {
        val owner = seller()
        whenever(memberRepository.findBySellerIdAndStatus(1L, SellerMemberEntity.STATUS_ACTIVE))
            .thenReturn(
                listOf(
                    SellerMemberEntity(
                        seller = owner,
                        tgUserId = 201L,
                        username = "a",
                        status = SellerMemberEntity.STATUS_ACTIVE,
                    ),
                    SellerMemberEntity(
                        seller = owner,
                        tgUserId = 202L,
                        username = "b",
                        status = SellerMemberEntity.STATUS_ACTIVE,
                    ),
                ),
            )

        val ids = teamService.listNotifyTgUserIds(owner)

        assertEquals(listOf(100L, 201L, 202L), ids)
    }
}
