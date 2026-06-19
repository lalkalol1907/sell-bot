package com.sellbot.core.service

import com.sellbot.core.domain.MonitoredChatEntity
import com.sellbot.core.domain.WorkerEntity
import com.sellbot.core.repository.MonitoredChatRepository
import com.sellbot.core.repository.WorkerRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.Instant

data class ChatSyncInput(
    val chatId: Long,
    val title: String?,
    val type: String?,
)

data class WhitelistEntry(
    val chatId: Long,
    val isActive: Boolean,
)

@Service
class WorkersService(
    private val workerRepository: WorkerRepository,
    private val monitoredChatRepository: MonitoredChatRepository,
    private val catalogService: CatalogService,
) {
    @Transactional
    fun createWorker(
        ownerSellerId: Long,
        tgAccountId: Long?,
        phone: String?,
        sessionEnc: ByteArray?,
        proxy: String?,
    ): WorkerEntity {
        val seller = catalogService.getSeller(ownerSellerId)
        return workerRepository.save(
            WorkerEntity(
                ownerSeller = seller,
                tgAccountId = tgAccountId,
                phone = phone,
                sessionEnc = sessionEnc,
                proxy = proxy,
                status = "active",
                lastSeenAt = Instant.now(),
            )
        )
    }

    fun listWorkers(ownerSellerId: Long): List<WorkerEntity> =
        workerRepository.findByOwnerSellerId(ownerSellerId)

    fun getActiveWorkers(): List<WorkerEntity> =
        workerRepository.findByStatus("active")

    @Transactional
    fun updateStatus(id: Long, status: String): WorkerEntity {
        val worker = workerRepository.findById(id).orElseThrow { IllegalArgumentException("Worker not found: $id") }
        worker.status = status
        if (status == "active") worker.lastSeenAt = Instant.now()
        return workerRepository.save(worker)
    }

    @Transactional
    fun syncChats(workerId: Long, chats: List<ChatSyncInput>): Int {
        val worker = workerRepository.findById(workerId).orElseThrow { IllegalArgumentException("Worker not found") }
        var synced = 0
        for (chat in chats) {
            val existing = monitoredChatRepository.findByWorkerIdAndChatId(workerId, chat.chatId)
            if (existing != null) {
                existing.title = chat.title
                existing.type = chat.type
                monitoredChatRepository.save(existing)
            } else {
                monitoredChatRepository.save(
                    MonitoredChatEntity(
                        worker = worker,
                        chatId = chat.chatId,
                        title = chat.title,
                        type = chat.type,
                        isActive = false,
                    )
                )
            }
            synced++
        }
        return synced
    }

    fun listChats(workerId: Long, ownerSellerId: Long): List<MonitoredChatEntity> {
        workerRepository.findByIdAndOwnerSellerId(workerId, ownerSellerId)
            ?: throw IllegalArgumentException("Worker not found or access denied")
        return monitoredChatRepository.findByWorkerIdOrderByIsActiveDescTitleAsc(workerId)
    }

    fun getWorkerSession(workerId: Long): ByteArray? {
        val worker = workerRepository.findById(workerId).orElse(null)
            ?: throw IllegalArgumentException("Worker not found: $workerId")
        return worker.sessionEnc
    }

    @Transactional
    fun setChatWhitelist(workerId: Long, ownerSellerId: Long, entries: List<WhitelistEntry>): Int {
        workerRepository.findByIdAndOwnerSellerId(workerId, ownerSellerId)
            ?: throw IllegalArgumentException("Worker not found or access denied")
        var updated = 0
        for (entry in entries) {
            val chat = monitoredChatRepository.findByWorkerIdAndChatId(workerId, entry.chatId) ?: continue
            chat.isActive = entry.isActive
            monitoredChatRepository.save(chat)
            updated++
        }
        return updated
    }
}
