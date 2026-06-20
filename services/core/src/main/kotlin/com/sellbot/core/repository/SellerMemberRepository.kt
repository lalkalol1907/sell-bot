package com.sellbot.core.repository

import com.sellbot.core.domain.SellerMemberEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param

interface SellerMemberRepository : JpaRepository<SellerMemberEntity, Long> {
    fun findBySellerIdOrderByCreatedAtDesc(sellerId: Long): List<SellerMemberEntity>

    fun findBySellerIdAndId(sellerId: Long, id: Long): SellerMemberEntity?

    fun findBySellerIdAndUsernameIgnoreCase(sellerId: Long, username: String): SellerMemberEntity?

    fun findByTgUserIdAndStatus(tgUserId: Long, status: String): SellerMemberEntity?

    @Query(
        """
        SELECT m FROM SellerMemberEntity m
        WHERE LOWER(m.username) = LOWER(:username) AND m.status = :status
        ORDER BY m.createdAt ASC
        """
    )
    fun findByUsernameIgnoreCaseAndStatus(
        @Param("username") username: String,
        @Param("status") status: String,
    ): List<SellerMemberEntity>

    fun findBySellerIdAndStatus(sellerId: Long, status: String): List<SellerMemberEntity>
}
