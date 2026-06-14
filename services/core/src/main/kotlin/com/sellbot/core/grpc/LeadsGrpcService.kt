package com.sellbot.core.grpc

import com.sellbot.core.domain.LeadEntity
import com.sellbot.core.service.CreateLeadInput
import com.sellbot.core.service.LeadsService
import com.sellbot.proto.leads.CreateLeadRequest
import com.sellbot.proto.leads.GetLeadStatsRequest
import com.sellbot.proto.leads.Lead
import com.sellbot.proto.leads.LeadStats
import com.sellbot.proto.leads.LeadsServiceGrpc
import com.sellbot.proto.leads.ListLeadsRequest
import com.sellbot.proto.leads.ListLeadsResponse
import com.sellbot.proto.leads.UpdateLeadStatusRequest
import io.grpc.Status
import io.grpc.stub.StreamObserver
import net.devh.boot.grpc.server.service.GrpcService
import java.math.BigDecimal

@GrpcService
class LeadsGrpcService(
    private val leadsService: LeadsService,
) : LeadsServiceGrpc.LeadsServiceImplBase() {

    override fun createLead(request: CreateLeadRequest, responseObserver: StreamObserver<Lead>) {
        try {
            val lead = leadsService.createLead(
                CreateLeadInput(
                    sellerId = request.sellerId,
                    productId = request.productId.takeIf { it != 0L },
                    workerId = request.workerId.takeIf { it != 0L },
                    chatId = request.chatId,
                    messageId = request.messageId,
                    authorId = request.authorId,
                    authorUsername = request.authorUsername.ifBlank { null },
                    rawText = request.rawText,
                    matchedKeywords = request.matchedKeywordsList,
                    productScore = BigDecimal.valueOf(request.productScore),
                    intentScore = BigDecimal.valueOf(request.intentScore),
                    score = BigDecimal.valueOf(request.score),
                    level = request.level,
                    productTitle = request.productTitle,
                    chatTitle = request.chatTitle,
                )
            )
            responseObserver.onNext(lead.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.INVALID_ARGUMENT.withDescription(e.message).asRuntimeException())
        }
    }

    override fun updateLeadStatus(request: UpdateLeadStatusRequest, responseObserver: StreamObserver<Lead>) {
        try {
            val lead = leadsService.updateStatus(request.id, request.sellerId, request.status)
            responseObserver.onNext(lead.toProto())
            responseObserver.onCompleted()
        } catch (e: Exception) {
            responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
        }
    }

    override fun listLeads(request: ListLeadsRequest, responseObserver: StreamObserver<ListLeadsResponse>) {
        val limit = if (request.limit > 0) request.limit else 20
        val offset = request.offset.coerceAtLeast(0)
        val (leads, total) = leadsService.listLeads(request.sellerId, request.status, limit, offset)
        responseObserver.onNext(
            ListLeadsResponse.newBuilder()
                .addAllLeads(leads.map { it.toProto() })
                .setTotal(total)
                .build()
        )
        responseObserver.onCompleted()
    }

    override fun getLeadStats(request: GetLeadStatsRequest, responseObserver: StreamObserver<LeadStats>) {
        val days = if (request.days > 0) request.days else 30
        val stats = leadsService.getStats(request.sellerId, days)
        responseObserver.onNext(
            LeadStats.newBuilder()
                .setTotal(stats.total)
                .setNewCount(stats.newCount)
                .setContacted(stats.contacted)
                .setClosed(stats.closed)
                .setSpam(stats.spam)
                .build()
        )
        responseObserver.onCompleted()
    }

    private fun LeadEntity.toProto(): Lead = Lead.newBuilder()
        .setId(id!!)
        .setSellerId(seller.id!!)
        .setProductId(product?.id ?: 0)
        .setWorkerId(worker?.id ?: 0)
        .setChatId(chatId)
        .setMessageId(messageId)
        .setAuthorId(authorId)
        .setAuthorUsername(authorUsername ?: "")
        .setRawText(rawText)
        .addAllMatchedKeywords(matchedKeywords.toList())
        .setProductScore(productScore.toDouble())
        .setIntentScore(intentScore.toDouble())
        .setScore(score.toDouble())
        .setLevel(level)
        .setStatus(status)
        .build()
}
