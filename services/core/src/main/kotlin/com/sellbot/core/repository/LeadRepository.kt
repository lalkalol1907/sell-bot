package com.sellbot.core.repository

import com.sellbot.core.domain.LeadEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import java.time.Instant

interface LeadRepository : JpaRepository<LeadEntity, Long> {
    fun findBySellerIdOrderByCreatedAtDesc(sellerId: Long): List<LeadEntity>

    fun findBySellerIdAndStatusOrderByCreatedAtDesc(sellerId: Long, status: String): List<LeadEntity>

    fun findByIdAndSellerId(id: Long, sellerId: Long): LeadEntity?

    @Query(
        """
        SELECT COUNT(l) FROM LeadEntity l
        WHERE l.seller.id = :sellerId AND l.createdAt >= :since
        """
    )
    fun countBySellerSince(sellerId: Long, since: Instant): Long

    @Query(
        """
        SELECT COUNT(l) FROM LeadEntity l
        WHERE l.seller.id = :sellerId AND l.status = :status AND l.createdAt >= :since
        """
    )
    fun countBySellerStatusSince(sellerId: Long, status: String, since: Instant): Long
}
