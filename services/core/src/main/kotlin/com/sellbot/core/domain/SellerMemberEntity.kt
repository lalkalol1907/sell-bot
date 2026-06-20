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
@Table(name = "seller_members")
class SellerMemberEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "seller_id", nullable = false)
    var seller: SellerEntity,

    @Column(name = "tg_user_id")
    var tgUserId: Long? = null,

    @Column(nullable = false)
    var username: String,

    @Column(name = "full_name")
    var fullName: String? = null,

    @Column(nullable = false)
    var status: String = STATUS_PENDING,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),

    @Column(name = "joined_at")
    var joinedAt: Instant? = null,
) {
    companion object {
        const val STATUS_PENDING = "pending"
        const val STATUS_ACTIVE = "active"
    }
}
