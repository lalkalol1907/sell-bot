package com.sellbot.core.repository

import com.sellbot.core.domain.ProductEntity
import org.springframework.data.jpa.repository.JpaRepository

interface ProductRepository : JpaRepository<ProductEntity, Long> {
    fun findBySellerIdAndIsActiveTrue(sellerId: Long): List<ProductEntity>
    fun findBySellerId(sellerId: Long): List<ProductEntity>
    fun findByIdAndSellerId(id: Long, sellerId: Long): ProductEntity?
}
