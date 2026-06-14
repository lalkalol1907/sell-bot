package com.sellbot.core.repository

import com.sellbot.core.domain.SellerEntity
import org.springframework.data.jpa.repository.JpaRepository
import java.util.Optional

interface SellerRepository : JpaRepository<SellerEntity, Long> {
    fun findByTgUserId(tgUserId: Long): Optional<SellerEntity>
}
