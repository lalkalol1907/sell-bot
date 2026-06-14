package com.sellbot.core.domain

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.Instant

@Entity
@Table(name = "sellers")
class SellerEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @Column(name = "tg_user_id", nullable = false, unique = true)
    var tgUserId: Long,

    @Column
    var username: String? = null,

    @Column(name = "full_name")
    var fullName: String? = null,

    @Column(nullable = false)
    var plan: String = "free",

    @Column(nullable = false)
    var sensitivity: String = "precise",

    @Column(name = "is_active", nullable = false)
    var isActive: Boolean = true,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
