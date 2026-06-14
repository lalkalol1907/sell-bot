package com.sellbot.core.grpc

import io.grpc.Context
import io.grpc.Contexts
import io.grpc.Metadata
import io.grpc.ServerCall
import io.grpc.ServerCallHandler
import io.grpc.ServerInterceptor
import net.devh.boot.grpc.server.interceptor.GrpcGlobalServerInterceptor

@GrpcGlobalServerInterceptor
class InternalGrpcAuthInterceptor : ServerInterceptor {
    override fun <ReqT : Any?, RespT : Any?> interceptCall(
        call: ServerCall<ReqT, RespT>,
        headers: Metadata,
        next: ServerCallHandler<ReqT, RespT>,
    ): ServerCall.Listener<ReqT> {
        val token = headers.get(InternalGrpcMetadata.METADATA_KEY) ?: ""
        val ctx = Context.current().withValue(InternalGrpcMetadata.CONTEXT_KEY, token)
        return Contexts.interceptCall(ctx, call, headers, next)
    }
}
