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
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.math.BigDecimal
import java.time.Instant

@Entity
@Table(name = "leads")
class LeadEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "seller_id", nullable = false)
    var seller: SellerEntity,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id")
    var product: ProductEntity? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "worker_id")
    var worker: WorkerEntity? = null,

    @Column(name = "chat_id", nullable = false)
    var chatId: Long,

    @Column(name = "message_id", nullable = false)
    var messageId: Long,

    @Column(name = "author_id", nullable = false)
    var authorId: Long,

    @Column(name = "author_username")
    var authorUsername: String? = null,

    @Column(name = "raw_text", nullable = false)
    var rawText: String,

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "matched_keywords", columnDefinition = "text[]", nullable = false)
    var matchedKeywords: Array<String> = emptyArray(),

    @Column(name = "product_score", nullable = false)
    var productScore: BigDecimal = BigDecimal.ZERO,

    @Column(name = "intent_score", nullable = false)
    var intentScore: BigDecimal = BigDecimal.ZERO,

    @Column(nullable = false)
    var score: BigDecimal = BigDecimal.ZERO,

    @Column(nullable = false)
    var level: String,

    @Column(nullable = false)
    var status: String = "new",

    @Column(name = "created_at", nullable = false)
    var createdAt: Instant = Instant.now(),
)
