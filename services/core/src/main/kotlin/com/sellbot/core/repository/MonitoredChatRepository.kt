package com.sellbot.core.repository

import com.sellbot.core.domain.MonitoredChatEntity
import org.springframework.data.jpa.repository.JpaRepository

interface MonitoredChatRepository : JpaRepository<MonitoredChatEntity, Long> {
    fun findByWorkerId(workerId: Long): List<MonitoredChatEntity>
    fun findByWorkerIdAndIsActiveTrue(workerId: Long): List<MonitoredChatEntity>
    fun findByWorkerIdAndChatId(workerId: Long, chatId: Long): MonitoredChatEntity?
}
