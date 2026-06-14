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
import java.time.Instant

@Entity
@Table(name = "workers")
class WorkerEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "owner_seller_id", nullable = false)
    var ownerSeller: SellerEntity,

    @Column(name = "tg_account_id")
    var tgAccountId: Long? = null,

    @Column
    var phone: String? = null,

    @Column(name = "session_enc")
    var sessionEnc: ByteArray? = null,

    @Column
    var proxy: String? = null,

    @Column(nullable = false)
    var status: String = "paused",

    @Column(name = "last_seen_at")
    var lastSeenAt: Instant? = null,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
