package com.sellbot.core.http

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "sellbot")
data class SellbotHttpProperties(
    val internalGrpcToken: String = "",
    val botToken: String = "",
    val secureCookies: Boolean = false,
    val jwt: JwtProperties = JwtProperties(),
    val corsOrigins: String = "http://localhost:8081,http://localhost:8082",
    val loginWebUrl: String = "http://localhost:8081/miniapp/",
    val loginRouteTtlSec: Long = 600,
    val workerLoginGrpcAddrs: String = "worker-engine:50053",
) {
    data class JwtProperties(
        val secret: String = "dev-jwt-secret-change-me",
        val ttlHours: Long = 168,
    )

    fun corsOriginList(): List<String> =
        corsOrigins.split(",").map { it.trim() }.filter { it.isNotEmpty() }

    fun workerLoginAddrs(): List<String> =
        workerLoginGrpcAddrs.split(",").map { it.trim() }.filter { it.isNotEmpty() }
}
