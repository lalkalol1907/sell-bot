package com.sellbot.core.http.grpc

import com.sellbot.core.grpc.InternalGrpcMetadata
import com.sellbot.core.http.SellbotHttpProperties
import com.sellbot.proto.workerlogin.GetLoginStatusRequest
import com.sellbot.proto.workerlogin.LoginStepResponse
import com.sellbot.proto.workerlogin.StartLoginRequest
import com.sellbot.proto.workerlogin.StartQRLoginRequest
import com.sellbot.proto.workerlogin.SubmitCodeRequest
import com.sellbot.proto.workerlogin.SubmitPasswordRequest
import com.sellbot.proto.workerlogin.WorkerLoginServiceGrpc
import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import io.grpc.stub.MetadataUtils
import jakarta.annotation.PreDestroy
import org.springframework.stereotype.Component
import java.util.concurrent.ConcurrentHashMap

data class LoginStep(
    val loginId: String,
    val status: String,
    val message: String,
    val workerId: Long,
    val qrUrl: String,
    val qrExpiresAt: Long,
)

@Component
class WorkerLoginClient(
    properties: SellbotHttpProperties,
) {
    private val internalToken = properties.internalGrpcToken
    private val channels = ConcurrentHashMap<String, ManagedChannel>()

    fun startQrLogin(engineAddr: String, ownerSellerId: Long): LoginStep {
        val stub = blockingStub(engineAddr)
        val response = stub.startQRLogin(
            StartQRLoginRequest.newBuilder().setOwnerSellerId(ownerSellerId).build(),
        )
        return response.toLoginStep()
    }

    fun startPhoneLogin(engineAddr: String, ownerSellerId: Long, phone: String): LoginStep {
        val stub = blockingStub(engineAddr)
        val response = stub.startLogin(
            StartLoginRequest.newBuilder()
                .setOwnerSellerId(ownerSellerId)
                .setPhone(phone)
                .build(),
        )
        return response.toLoginStep()
    }

    fun submitCode(engineAddr: String, loginId: String, code: String): LoginStep {
        val stub = blockingStub(engineAddr)
        val response = stub.submitCode(
            SubmitCodeRequest.newBuilder().setLoginId(loginId).setCode(code).build(),
        )
        return response.toLoginStep()
    }

    fun submitPassword(engineAddr: String, loginId: String, password: String): LoginStep {
        val stub = blockingStub(engineAddr)
        val response = stub.submitPassword(
            SubmitPasswordRequest.newBuilder().setLoginId(loginId).setPassword(password).build(),
        )
        return response.toLoginStep()
    }

    fun getLoginStatus(engineAddr: String, loginId: String): LoginStep {
        val stub = blockingStub(engineAddr)
        val response = stub.getLoginStatus(
            GetLoginStatusRequest.newBuilder().setLoginId(loginId).build(),
        )
        return response.toLoginStep()
    }

    private fun blockingStub(engineAddr: String): WorkerLoginServiceGrpc.WorkerLoginServiceBlockingStub {
        val channel = channels.computeIfAbsent(engineAddr) { addr ->
            ManagedChannelBuilder.forTarget(addr)
                .usePlaintext()
                .build()
        }
        var stub = WorkerLoginServiceGrpc.newBlockingStub(channel)
        if (internalToken.isNotBlank()) {
            val metadata = io.grpc.Metadata()
            metadata.put(InternalGrpcMetadata.METADATA_KEY, internalToken)
            stub = stub.withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
        }
        return stub
    }

    @PreDestroy
    fun shutdown() {
        channels.values.forEach { it.shutdown() }
        channels.clear()
    }

    private fun LoginStepResponse.toLoginStep() = LoginStep(
        loginId = loginId,
        status = status,
        message = message,
        workerId = workerId,
        qrUrl = qrUrl,
        qrExpiresAt = qrExpiresAt,
    )
}
