package com.sellbot.core.http.redis

import org.springframework.data.redis.core.StringRedisTemplate
import org.springframework.stereotype.Component
import java.time.Duration

@Component
class RateLimiter(
    private val redis: StringRedisTemplate,
) {
    fun allow(key: String, limit: Int, windowMs: Long): Boolean {
        val redisKey = "rl:$key"
        val count = redis.opsForValue().increment(redisKey) ?: return false
        if (count == 1L) {
            redis.expire(redisKey, Duration.ofMillis(windowMs))
        }
        return count <= limit
    }
}
