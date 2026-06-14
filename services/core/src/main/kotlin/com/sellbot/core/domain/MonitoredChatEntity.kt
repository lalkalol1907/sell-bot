package com.sellbot.core.domain

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.FetchType
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.JoinColumn
import jakarta.persistence.ManyToOne
import jakarta.persistence.Table

@Entity
@Table(name = "monitored_chats")
class MonitoredChatEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "worker_id", nullable = false)
    var worker: WorkerEntity,

    @Column(name = "chat_id", nullable = false)
    var chatId: Long,

    @Column
    var title: String? = null,

    @Column
    var type: String? = null,

    @Column(name = "is_active", nullable = false)
    var isActive: Boolean = false,
)
