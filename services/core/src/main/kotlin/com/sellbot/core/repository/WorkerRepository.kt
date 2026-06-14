package com.sellbot.core.repository

import com.sellbot.core.domain.WorkerEntity
import org.springframework.data.jpa.repository.JpaRepository

interface WorkerRepository : JpaRepository<WorkerEntity, Long> {
    fun findByOwnerSellerId(ownerSellerId: Long): List<WorkerEntity>
    fun findByStatus(status: String): List<WorkerEntity>
    fun findByIdAndOwnerSellerId(id: Long, ownerSellerId: Long): WorkerEntity?
}
