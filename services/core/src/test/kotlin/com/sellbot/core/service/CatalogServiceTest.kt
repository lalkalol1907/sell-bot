package com.sellbot.core.service

import com.sellbot.core.domain.ProductEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.repository.ProductRepository
import com.sellbot.core.repository.SellerRepository
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.junit.jupiter.MockitoExtension
import org.mockito.kotlin.any
import org.mockito.kotlin.eq
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import java.math.BigDecimal
import java.util.Optional

@ExtendWith(MockitoExtension::class)
class CatalogServiceTest {

    @Mock
    lateinit var sellerRepository: SellerRepository

    @Mock
    lateinit var productRepository: ProductRepository

    @Mock
    lateinit var spamLearningService: SpamLearningService

    @InjectMocks
    lateinit var catalogService: CatalogService

    private val seller = SellerEntity(id = 1L, tgUserId = 100L)

    @Test
    fun `createOrGetSeller returns existing seller`() {
        whenever(sellerRepository.findByTgUserId(100L)).thenReturn(Optional.of(seller))

        val result = catalogService.createOrGetSeller(100L, "user", "Name")

        assertEquals(1L, result.id)
        verify(sellerRepository, never()).save(any())
    }

    @Test
    fun `createOrGetSeller creates new seller`() {
        whenever(sellerRepository.findByTgUserId(200L)).thenReturn(Optional.empty())
        whenever(sellerRepository.save(any<SellerEntity>())).thenAnswer { invocation ->
            invocation.getArgument<SellerEntity>(0)
        }

        val result = catalogService.createOrGetSeller(200L, "newuser", "New")

        assertEquals(200L, result.tgUserId)
        verify(sellerRepository).save(any())
    }

    @Test
    fun `createProduct expands iPhone keywords`() {
        whenever(sellerRepository.findById(1L)).thenReturn(Optional.of(seller))
        whenever(productRepository.save(any<ProductEntity>())).thenAnswer { invocation ->
            val product = invocation.getArgument<ProductEntity>(0)
            product.id = 10L
            product
        }

        val product = catalogService.createProduct(
            sellerId = 1L,
            title = "iPhone 16 Pro",
            price = BigDecimal("99990"),
            currency = "RUB",
            keywords = listOf("16 pro"),
        )

        assertEquals("iPhone 16 Pro", product.title)
        assertTrue(product.keywords.contains("iphone"))
        assertTrue(product.keywords.contains("айфон"))
        assertTrue(product.keywords.contains("16 pro"))
        assertTrue(product.keywords.contains("iphone 16 pro"))
    }

    @Test
    fun `updateProduct throws when not found`() {
        whenever(productRepository.findByIdAndSellerId(99L, 1L)).thenReturn(null)

        assertThrows(IllegalArgumentException::class.java) {
            catalogService.updateProduct(99L, 1L, "X", BigDecimal.ONE, "RUB", emptyList(), true)
        }
    }

    @Test
    fun `deleteProduct returns false when missing`() {
        whenever(productRepository.findByIdAndSellerId(5L, 1L)).thenReturn(null)

        assertFalse(catalogService.deleteProduct(5L, 1L))
    }

    @Test
    fun `deleteProduct returns true when found`() {
        val product = ProductEntity(id = 5L, seller = seller, title = "X", price = BigDecimal.ONE)
        whenever(productRepository.findByIdAndSellerId(5L, 1L)).thenReturn(product)

        assertTrue(catalogService.deleteProduct(5L, 1L))
        verify(productRepository).delete(product)
    }
}
