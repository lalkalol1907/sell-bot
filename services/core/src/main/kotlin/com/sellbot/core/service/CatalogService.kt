package com.sellbot.core.service

import com.sellbot.core.domain.ProductEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.ProductRepository
import com.sellbot.core.repository.SellerRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.math.BigDecimal

@Service
class CatalogService(
    private val sellerRepository: SellerRepository,
    private val productRepository: ProductRepository,
) {
    @Transactional
    fun createOrGetSeller(tgUserId: Long, username: String?, fullName: String?): SellerEntity {
        return sellerRepository.findByTgUserId(tgUserId).orElseGet {
            sellerRepository.save(
                SellerEntity(
                    tgUserId = tgUserId,
                    username = username,
                    fullName = fullName,
                )
            )
        }
    }

    fun getSellerByTgId(tgUserId: Long): SellerEntity? =
        sellerRepository.findByTgUserId(tgUserId).orElse(null)

    fun getSeller(id: Long): SellerEntity =
        sellerRepository.findById(id).orElseThrow { IllegalArgumentException("Seller not found: $id") }

    @Transactional
    fun createProduct(
        sellerId: Long,
        title: String,
        price: BigDecimal,
        currency: String,
        keywords: List<String>,
    ): ProductEntity {
        val seller = getSeller(sellerId)
        val normalizedKeywords = normalizeKeywords(title, keywords)
        return productRepository.save(
            ProductEntity(
                seller = seller,
                title = title,
                price = price,
                currency = currency,
                keywords = normalizedKeywords.toTypedArray(),
            )
        )
    }

    @Transactional
    fun updateProduct(
        id: Long,
        sellerId: Long,
        title: String,
        price: BigDecimal,
        currency: String,
        keywords: List<String>,
        isActive: Boolean,
    ): ProductEntity {
        val product = productRepository.findByIdAndSellerId(id, sellerId)
            ?: throw IllegalArgumentException("Product not found: $id")
        product.title = title
        product.price = price
        product.currency = currency
        product.keywords = normalizeKeywords(title, keywords).toTypedArray()
        product.isActive = isActive
        return productRepository.save(product)
    }

    fun listProducts(sellerId: Long, activeOnly: Boolean): List<ProductEntity> =
        if (activeOnly) productRepository.findBySellerIdAndIsActiveTrue(sellerId)
        else productRepository.findBySellerId(sellerId)

    @Transactional
    fun deleteProduct(id: Long, sellerId: Long): Boolean {
        val product = productRepository.findByIdAndSellerId(id, sellerId) ?: return false
        productRepository.delete(product)
        return true
    }

    private fun normalizeKeywords(title: String, keywords: List<String>): List<String> {
        val base = linkedSetOf<String>()
        base.add(title.lowercase().trim())
        keywords.map { it.lowercase().trim() }.filter { it.isNotBlank() }.forEach { base.add(it) }
        if (title.contains("iphone", ignoreCase = true) || title.contains("айфон", ignoreCase = true)) {
            base.add("iphone")
            base.add("айфон")
        }
        return base.toList()
    }
}
