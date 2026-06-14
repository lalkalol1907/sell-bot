package com.sellbot.core.service

import com.sellbot.core.domain.MonitoredChatEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.domain.WorkerEntity
import com.sellbot.core.repository.MonitoredChatRepository
import com.sellbot.core.repository.WorkerRepository
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.junit.jupiter.MockitoExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import java.util.Optional

@ExtendWith(MockitoExtension::class)
class WorkersServiceTest {

    @Mock
    lateinit var workerRepository: WorkerRepository

    @Mock
    lateinit var monitoredChatRepository: MonitoredChatRepository

    @Mock
    lateinit var catalogService: CatalogService

    @InjectMocks
    lateinit var workersService: WorkersService

    private val seller = SellerEntity(id = 1L, tgUserId = 100L)
    private val worker = WorkerEntity(id = 5L, ownerSeller = seller, phone = "+7999")

    @Test
    fun `syncChats creates new chat as inactive`() {
        whenever(workerRepository.findById(5L)).thenReturn(Optional.of(worker))
        whenever(monitoredChatRepository.findByWorkerIdAndChatId(5L, 1000L)).thenReturn(null)
        whenever(monitoredChatRepository.save(any<MonitoredChatEntity>())).thenAnswer { invocation ->
            invocation.getArgument<MonitoredChatEntity>(0)
        }

        val synced = workersService.syncChats(
            workerId = 5L,
            chats = listOf(ChatSyncInput(chatId = 1000L, title = "Test Group", type = "group")),
        )

        assertEquals(1, synced)
        verify(monitoredChatRepository).save(any())
    }

    @Test
    fun `syncChats updates existing chat title`() {
        val existing = MonitoredChatEntity(
            id = 1L,
            worker = worker,
            chatId = 1000L,
            title = "Old",
            type = "group",
            isActive = true,
        )
        whenever(workerRepository.findById(5L)).thenReturn(Optional.of(worker))
        whenever(monitoredChatRepository.findByWorkerIdAndChatId(5L, 1000L)).thenReturn(existing)
        whenever(monitoredChatRepository.save(existing)).thenReturn(existing)

        workersService.syncChats(
            workerId = 5L,
            chats = listOf(ChatSyncInput(chatId = 1000L, title = "New Title", type = "group")),
        )

        assertEquals("New Title", existing.title)
    }

    @Test
    fun `setChatWhitelist updates active flag`() {
        val chat = MonitoredChatEntity(id = 1L, worker = worker, chatId = 1000L, isActive = false)
        whenever(workerRepository.findByIdAndOwnerSellerId(5L, 1L)).thenReturn(worker)
        whenever(monitoredChatRepository.findByWorkerIdAndChatId(5L, 1000L)).thenReturn(chat)
        whenever(monitoredChatRepository.save(chat)).thenReturn(chat)

        val updated = workersService.setChatWhitelist(
            workerId = 5L,
            ownerSellerId = 1L,
            entries = listOf(WhitelistEntry(chatId = 1000L, isActive = true)),
        )

        assertEquals(1, updated)
        assertEquals(true, chat.isActive)
    }

    @Test
    fun `listChats denies foreign seller`() {
        whenever(workerRepository.findByIdAndOwnerSellerId(5L, 99L)).thenReturn(null)

        assertThrows(IllegalArgumentException::class.java) {
            workersService.listChats(5L, 99L)
        }
    }

    @Test
    fun `getWorkerSession returns encrypted bytes`() {
        val session = byteArrayOf(1, 2, 3)
        worker.sessionEnc = session
        whenever(workerRepository.findById(5L)).thenReturn(Optional.of(worker))

        assertEquals(session, workersService.getWorkerSession(5L))
    }

    @Test
    fun `getWorkerSession returns null when empty`() {
        worker.sessionEnc = null
        whenever(workerRepository.findById(5L)).thenReturn(Optional.of(worker))

        assertNull(workersService.getWorkerSession(5L))
    }

    @Test
    fun `updateStatus active sets lastSeenAt`() {
        whenever(workerRepository.findById(5L)).thenReturn(Optional.of(worker))
        whenever(workerRepository.save(any<WorkerEntity>())).thenReturn(worker)

        val updated = workersService.updateStatus(5L, "active")

        assertEquals("active", updated.status)
        assertEquals(true, updated.lastSeenAt != null)
    }
}
