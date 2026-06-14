package com.sellbot.core.grpc

import com.sellbot.core.domain.ProductEntity
import com.sellbot.core.domain.SellerEntity
import com.sellbot.core.service.CatalogService
import com.sellbot.proto.catalog.CatalogServiceGrpc
import com.sellbot.proto.catalog.CreateProductRequest
import com.sellbot.proto.catalog.CreateSellerRequest
import com.sellbot.proto.catalog.DeleteProductRequest
import com.sellbot.proto.catalog.DeleteProductResponse
import com.sellbot.proto.catalog.GetSellerByTgIdRequest
import com.sellbot.proto.catalog.GetSellerRequest
import com.sellbot.proto.catalog.ListProductsRequest
import com.sellbot.proto.catalog.ListProductsResponse
import com.sellbot.proto.catalog.Product
import com.sellbot.proto.catalog.Seller
import com.sellbot.proto.catalog.UpdateProductRequest
import io.grpc.Status
import io.grpc.stub.StreamObserver
import net.devh.boot.grpc.server.service.GrpcService
import java.math.BigDecimal

@GrpcService
class CatalogGrpcService(
    private val catalogService: CatalogService,
) : CatalogServiceGrpc.CatalogServiceImplBase() {

    override fun createSeller(request: CreateSellerRequest, responseObserver: StreamObserver<Seller>) {
        try {
            val seller = catalogService.createOrGetSeller(
                tgUserId = request.tgUserId,
                username = request.username.ifBlank { null },
                fullName = request.fullName.ifBlank { null },
            )
            responseObserver.onNext(seller.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INTERNAL.withDescription(e.message).asRuntimeException())
        }
    }

    override fun getSellerByTgId(request: GetSellerByTgIdRequest, responseObserver: StreamObserver<Seller>) {
        val seller = catalogService.getSellerByTgId(request.tgUserId)
        if (seller == null) {
            responseObserver.onError(Status.NOT_FOUND.asRuntimeException())
            return
        }
        responseObserver.onNext(seller.toProto())
        responseObserver.onCompleted()
    }

    override fun getSeller(request: GetSellerRequest, responseObserver: StreamObserver<Seller>) {
        try {
            val seller = catalogService.getSeller(request.id)
            responseObserver.onNext(seller.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
        }
    }

    override fun createProduct(request: CreateProductRequest, responseObserver: StreamObserver<Product>) {
        try {
            val product = catalogService.createProduct(
                sellerId = request.sellerId,
                title = request.title,
                price = BigDecimal(request.price),
                currency = request.currency.ifBlank { "RUB" },
                keywords = request.keywordsList,
            )
            responseObserver.onNext(product.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(e.message).asRuntimeException())
        }
    }

    override fun updateProduct(request: UpdateProductRequest, responseObserver: StreamObserver<Product>) {
        try {
            val product = catalogService.updateProduct(
                id = request.id,
                sellerId = request.sellerId,
                title = request.title,
                price = BigDecimal(request.price),
                currency = request.currency.ifBlank { "RUB" },
                keywords = request.keywordsList,
                isActive = request.isActive,
            )
            responseObserver.onNext(product.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(e.message).asRuntimeException())
        }
    }

    override fun listProducts(request: ListProductsRequest, responseObserver: StreamObserver<ListProductsResponse>) {
        val products = catalogService.listProducts(request.sellerId, request.activeOnly)
        val response = ListProductsResponse.newBuilder()
            .addAllProducts(products.map { it.toProto() })
            .build()
        responseObserver.onNext(response)
        responseObserver.onCompleted()
    }

    override fun deleteProduct(request: DeleteProductRequest, responseObserver: StreamObserver<DeleteProductResponse>) {
        val success = catalogService.deleteProduct(request.id, request.sellerId)
        responseObserver.onNext(DeleteProductResponse.newBuilder().setSuccess(success).build())
        responseObserver.onCompleted()
    }

    private fun SellerEntity.toProto(): Seller = Seller.newBuilder()
        .setId(id!!)
        .setTgUserId(tgUserId)
        .setUsername(username ?: "")
        .setFullName(fullName ?: "")
        .setPlan(plan)
        .setSensitivity(sensitivity)
        .setIsActive(isActive)
        .build()

    private fun ProductEntity.toProto(): Product = Product.newBuilder()
        .setId(id!!)
        .setSellerId(seller.id!!)
        .setTitle(title)
        .setPrice(price.toPlainString())
        .setCurrency(currency)
        .addAllKeywords(keywords.toList())
        .setIsActive(isActive)
        .build()
}
