package com.sellbot.core.grpc

import io.grpc.Status
import io.grpc.StatusRuntimeException
import org.junit.jupiter.api.Assertions.assertDoesNotThrow
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class InternalGrpcAuthTest {

    @Test
    fun `allows any token when expected is blank`() {
        val auth = InternalGrpcAuth("")
        assertDoesNotThrow { auth.validate("") }
        assertDoesNotThrow { auth.validate("anything") }
    }

    @Test
    fun `rejects mismatched token`() {
        val auth = InternalGrpcAuth("secret")
        val ex = assertThrows(StatusRuntimeException::class.java) {
            auth.validate("wrong")
        }
        assertEquals(Status.UNAUTHENTICATED.code, ex.status.code)
    }

    @Test
    fun `accepts matching token`() {
        val auth = InternalGrpcAuth("secret")
        assertDoesNotThrow { auth.validate("secret") }
    }

    @Test
    fun `validateFromContext reads interceptor value`() {
        val auth = InternalGrpcAuth("secret")
        val ctx = io.grpc.Context.current().withValue(InternalGrpcMetadata.CONTEXT_KEY, "secret")
        val prev = ctx.attach()
        try {
            assertDoesNotThrow { auth.validateFromContext() }
        } finally {
            ctx.detach(prev)
        }
    }
}
