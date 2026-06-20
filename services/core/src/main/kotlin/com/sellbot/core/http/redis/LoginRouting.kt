package com.sellbot.core.http.redis

import com.sellbot.core.http.SellbotHttpProperties
import org.springframework.data.redis.core.StringRedisTemplate
import org.springframework.stereotype.Component
import java.time.Duration
import java.util.concurrent.atomic.AtomicInteger

@Component
class LoginRouting(
    private val redis: StringRedisTemplate,
    properties: SellbotHttpProperties,
) {
    private val ttl = Duration.ofSeconds(properties.loginRouteTtlSec)

    fun pin(loginId: String, engineAddr: String) {
        redis.opsForValue().set("$ROUTE_PREFIX$loginId", engineAddr, ttl)
    }

    fun resolve(loginId: String): String? =
        redis.opsForValue().get("$ROUTE_PREFIX$loginId")

    fun clear(loginId: String) {
        redis.delete("$ROUTE_PREFIX$loginId")
    }

    companion object {
        private const val ROUTE_PREFIX = "login:route:"

        fun pickEngineAddress(addresses: List<String>, seed: Int, counter: Int): String {
            require(addresses.isNotEmpty()) { "login engine pool requires at least one address" }
            val index = kotlin.math.abs(counter + seed) % addresses.size
            return addresses[index]
        }
    }
}

@Component
class LoginEnginePool(
    properties: SellbotHttpProperties,
) {
    private val addresses = properties.workerLoginAddrs().also {
        require(it.isNotEmpty()) { "WORKER_LOGIN_GRPC_ADDR must contain at least one address" }
    }
    private val counter = AtomicInteger(0)

    val size: Int get() = addresses.size

    fun pickForNewSession(seed: Int): String {
        val addr = LoginRouting.pickEngineAddress(addresses, seed, counter.getAndIncrement())
        return addr
    }
}
