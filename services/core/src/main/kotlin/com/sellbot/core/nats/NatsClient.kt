package com.sellbot.core.nats

import io.nats.client.Connection
import io.nats.client.JetStream
import io.nats.client.JetStreamApiException
import io.nats.client.Nats
import io.nats.client.Options
import io.nats.client.api.RetentionPolicy
import io.nats.client.api.StorageType
import io.nats.client.api.StreamConfiguration
import jakarta.annotation.PostConstruct
import jakarta.annotation.PreDestroy
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import java.io.IOException
import java.time.Duration

@Component
class NatsClient(
    @Value("\${sellbot.nats.url:nats://nats:4222}") private val natsUrl: String,
) {
    private val log = LoggerFactory.getLogger(NatsClient::class.java)
    private lateinit var connection: Connection
    private lateinit var jetStream: JetStream

    @PostConstruct
    fun connect() {
        connection = Nats.connect(
            Options.builder()
                .server(natsUrl)
                .maxReconnects(-1)
                .reconnectWait(Duration.ofSeconds(2))
                .build()
        )
        jetStream = connection.jetStream()
        ensureStream()
        log.info("connected to NATS at {}", natsUrl)
    }

    @PreDestroy
    fun close() {
        if (::connection.isInitialized) {
            connection.close()
        }
    }

    private fun ensureStream() {
        val jsm = connection.jetStreamManagement()
        val streamName = "SELLBOT"
        val config = StreamConfiguration.builder()
            .name(streamName)
            .subjects("lead.created", "worker.status", "message.captured")
            .storageType(StorageType.File)
            .retentionPolicy(RetentionPolicy.Limits)
            .maxAge(Duration.ofDays(7))
            .build()
        try {
            jsm.getStreamInfo(streamName)
        } catch (_: JetStreamApiException) {
            try {
                jsm.addStream(config)
                log.info("created JetStream stream {}", streamName)
            } catch (e: IOException) {
                throw IllegalStateException("failed to create stream $streamName", e)
            } catch (e: JetStreamApiException) {
                throw IllegalStateException("failed to create stream $streamName", e)
            }
        }
    }

    fun publish(subject: String, data: ByteArray) {
        jetStream.publish(subject, data)
    }
}
