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
@Table(name = "spam_phrases")
class SpamPhraseEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "seller_id", nullable = false)
    var seller: SellerEntity,

    @Column(nullable = false)
    var phrase: String,

    @Column(name = "source_lead_id")
    var sourceLeadId: Long? = null,

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
