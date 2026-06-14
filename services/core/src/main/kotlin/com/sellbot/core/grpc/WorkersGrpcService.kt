package com.sellbot.core.grpc

import com.sellbot.core.domain.MonitoredChatEntity
import com.sellbot.core.domain.WorkerEntity
import com.sellbot.core.service.ChatSyncInput
import com.sellbot.core.service.WhitelistEntry
import com.sellbot.core.service.WorkersService
import com.sellbot.proto.workers.CreateWorkerRequest
import com.sellbot.proto.workers.GetActiveWorkersRequest
import com.sellbot.proto.workers.GetWorkerSessionRequest
import com.sellbot.proto.workers.GetWorkerSessionResponse
import com.sellbot.proto.workers.ListChatsRequest
import com.sellbot.proto.workers.ListChatsResponse
import com.sellbot.proto.workers.ListWorkersRequest
import com.sellbot.proto.workers.ListWorkersResponse
import com.sellbot.proto.workers.MonitoredChat
import com.sellbot.proto.workers.SetChatWhitelistRequest
import com.sellbot.proto.workers.SetChatWhitelistResponse
import com.sellbot.proto.workers.SyncChatsRequest
import com.sellbot.proto.workers.SyncChatsResponse
import com.sellbot.proto.workers.UpdateWorkerStatusRequest
import com.sellbot.proto.workers.Worker
import com.sellbot.proto.workers.WorkersServiceGrpc
import io.grpc.Status
import io.grpc.StatusRuntimeException
import io.grpc.stub.StreamObserver
import net.devh.boot.grpc.server.service.GrpcService

@GrpcService
class WorkersGrpcService(
    private val workersService: WorkersService,
    private val internalGrpcAuth: InternalGrpcAuth,
) : WorkersServiceGrpc.WorkersServiceImplBase() {

    override fun createWorker(request: CreateWorkerRequest, responseObserver: StreamObserver<Worker>) {
        try {
            val worker = workersService.createWorker(
                ownerSellerId = request.ownerSellerId,
                tgAccountId = request.tgAccountId.takeIf { it != 0L },
                phone = request.phone.ifBlank { null },
                sessionEnc = request.sessionEnc.toByteArray().takeIf { request.sessionEnc.size() > 0 },
                proxy = request.proxy.ifBlank { null },
            )
            responseObserver.onNext(worker.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(e.message).asRuntimeException())
        }
    }

    override fun listWorkers(request: ListWorkersRequest, responseObserver: StreamObserver<ListWorkersResponse>) {
        val workers = workersService.listWorkers(request.ownerSellerId)
        responseObserver.onNext(
            ListWorkersResponse.newBuilder().addAllWorkers(workers.map { it.toProto() }).build()
        )
        responseObserver.onCompleted()
    }

    override fun getActiveWorkers(
        request: GetActiveWorkersRequest,
        responseObserver: StreamObserver<ListWorkersResponse>,
    ) {
        val workers = workersService.getActiveWorkers()
        responseObserver.onNext(
            ListWorkersResponse.newBuilder().addAllWorkers(workers.map { it.toProto() }).build()
        )
        responseObserver.onCompleted()
    }

    override fun updateWorkerStatus(request: UpdateWorkerStatusRequest, responseObserver: StreamObserver<Worker>) {
        try {
            val worker = workersService.updateStatus(request.id, request.status)
            responseObserver.onNext(worker.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
        }
    }

    override fun syncChats(request: SyncChatsRequest, responseObserver: StreamObserver<SyncChatsResponse>) {
        try {
            val synced = workersService.syncChats(
                workerId = request.workerId,
                chats = request.chatsList.map {
                    ChatSyncInput(chatId = it.chatId, title = it.title, type = it.type)
                },
            )
            responseObserver.onNext(SyncChatsResponse.newBuilder().setSynced(synced).build())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(e.message).asRuntimeException())
        }
    }

    override fun listChats(request: ListChatsRequest, responseObserver: StreamObserver<ListChatsResponse>) {
        try {
            val chats = workersService.listChats(request.workerId, request.ownerSellerId)
            responseObserver.onNext(
                ListChatsResponse.newBuilder().addAllChats(chats.map { it.toProto() }).build()
            )
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.PERMISSION_DENIED.withDescription(e.message).asRuntimeException())
        }
    }

    override fun setChatWhitelist(
        request: SetChatWhitelistRequest,
        responseObserver: StreamObserver<SetChatWhitelistResponse>,
    ) {
        try {
            val updated = workersService.setChatWhitelist(
                workerId = request.workerId,
                ownerSellerId = request.ownerSellerId,
                entries = request.entriesList.map { WhitelistEntry(chatId = it.chatId, isActive = it.isActive) },
            )
            responseObserver.onNext(SetChatWhitelistResponse.newBuilder().setUpdated(updated).build())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.PERMISSION_DENIED.withDescription(e.message).asRuntimeException())
        }
    }

    override fun getWorkerSession(
        request: GetWorkerSessionRequest,
        responseObserver: StreamObserver<GetWorkerSessionResponse>,
    ) {
        try {
            internalGrpcAuth.validateFromContext()
            val session = workersService.getWorkerSession(request.workerId)
            val builder = GetWorkerSessionResponse.newBuilder()
            if (session != null) {
                builder.sessionEnc = com.google.protobuf.ByteString.copyFrom(session)
            }
            responseObserver.onNext(builder.build())
            responseObserver.onCompleted()
        } catch (e: StatusRuntimeException) {
            responseObserver.onError(e)
        } catch (e: Exception) {
            responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
        }
    }

    private fun WorkerEntity.toProto(): Worker = Worker.newBuilder()
        .setId(id!!)
        .setOwnerSellerId(ownerSeller.id!!)
        .setTgAccountId(tgAccountId ?: 0)
        .setPhone(phone ?: "")
        .setProxy(proxy ?: "")
        .setStatus(status)
        .build()

    private fun MonitoredChatEntity.toProto(): MonitoredChat = MonitoredChat.newBuilder()
        .setId(id!!)
        .setWorkerId(worker.id!!)
        .setChatId(chatId)
        .setTitle(title ?: "")
        .setType(type ?: "")
        .setIsActive(isActive)
        .build()
}
