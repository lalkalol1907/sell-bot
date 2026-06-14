package com.sellbot.core.grpc

import io.grpc.Context
import io.grpc.Metadata

object InternalGrpcMetadata {
    const val KEY_NAME = "x-internal-grpc-token"

    val METADATA_KEY: Metadata.Key<String> =
        Metadata.Key.of(KEY_NAME, Metadata.ASCII_STRING_MARSHALLER)

    val CONTEXT_KEY: Context.Key<String> = Context.key(KEY_NAME)
}
