# frozen_string_literal: true

class RateLimiter
  def initialize(redis: RedisClient.instance)
    @redis = redis
  end

  def allow?(key, limit:, window_ms:)
    redis_key = "rl:#{key}"
    count = @redis.incr(redis_key)
    @redis.pexpire(redis_key, window_ms) if count == 1
    count <= limit
  end
end
