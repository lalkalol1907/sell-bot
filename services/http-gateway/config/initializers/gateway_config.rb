# frozen_string_literal: true

module GatewayConfig
  module_function

  def bot_token
    ENV.fetch("BOT_TOKEN", "")
  end

  def core_grpc_addr
    ENV.fetch("CORE_GRPC_ADDR", "core:50051")
  end

  def login_engine_addrs
    raw = ENV.fetch("WORKER_LOGIN_GRPC_ADDR", "worker-engine:50053")
    addrs = raw.split(",").map(&:strip).reject(&:empty?)
    raise "WORKER_LOGIN_GRPC_ADDR must contain at least one address" if addrs.empty?

    addrs
  end

  def internal_grpc_token
    ENV.fetch("INTERNAL_GRPC_TOKEN", "")
  end

  def redis_url
    ENV.fetch("REDIS_URL", "redis://redis:6379/0")
  end

  def login_route_ttl_sec
    ENV.fetch("LOGIN_ROUTE_TTL_SEC", "600").to_i
  end

  def jwt_secret
    ENV.fetch("JWT_SECRET", "dev-jwt-secret-change-me")
  end

  def jwt_ttl_hours
    ENV.fetch("JWT_TTL_HOURS", "168").to_i
  end

  def cors_origins
    raw = ENV.fetch("CORS_ORIGINS", "http://localhost:8080")
    raw.split(",").map(&:strip).reject(&:empty?)
  end
end
