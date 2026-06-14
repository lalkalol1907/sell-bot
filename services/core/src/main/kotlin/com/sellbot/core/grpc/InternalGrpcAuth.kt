package com.sellbot.core.grpc

import io.grpc.Status
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component

@Component
class InternalGrpcAuth(
    @Value("\${sellbot.internal-grpc-token:}") private val expectedToken: String,
) {
    fun validate(provided: String) {
        if (expectedToken.isBlank()) {
            return
        }
        if (provided != expectedToken) {
            throw Status.UNAUTHENTICATED.withDescription("invalid internal token").asRuntimeException()
        }
    }

    fun validateFromContext() {
        validate(InternalGrpcMetadata.CONTEXT_KEY.get() ?: "")
    }
}
