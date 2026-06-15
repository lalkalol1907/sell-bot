# frozen_string_literal: true

class LoginRouting
  ROUTE_PREFIX = "login:route:"

  def initialize(redis: RedisClient.instance, ttl_sec: GatewayConfig.login_route_ttl_sec)
    @redis = redis
    @ttl_sec = ttl_sec
  end

  def pin(login_id, engine_addr)
    @redis.set("#{ROUTE_PREFIX}#{login_id}", engine_addr, ex: @ttl_sec)
  end

  def resolve(login_id)
    @redis.get("#{ROUTE_PREFIX}#{login_id}")
  end

  def clear(login_id)
    @redis.del("#{ROUTE_PREFIX}#{login_id}")
  end

  def self.pick_engine_address(addresses, seed, counter)
    raise ArgumentError, "login engine pool requires at least one address" if addresses.empty?

    index = (counter + seed).abs % addresses.size
    addresses[index]
  end
end
