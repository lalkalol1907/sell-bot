# frozen_string_literal: true

require "singleton"

class RedisClient
  include Singleton

  def self.instance
    @instance ||= new.connection
  end

  def connection
    @connection ||= Redis.new(url: GatewayConfig.redis_url)
  end
end
