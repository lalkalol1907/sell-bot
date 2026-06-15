# frozen_string_literal: true

require "jwt"

class JwtSession
  COOKIE_NAME = "sellbot_jwt"

  def initialize(secret: GatewayConfig.jwt_secret, ttl_hours: GatewayConfig.jwt_ttl_hours)
    @secret = secret
    @ttl_hours = ttl_hours
  end

  def encode(seller_id:, tg_user_id:)
    payload = {
      seller_id: seller_id,
      tg_user_id: tg_user_id,
      exp: @ttl_hours.hours.from_now.to_i
    }
    JWT.encode(payload, @secret, "HS256")
  end

  def decode(token)
    return nil if token.blank?

    payload, = JWT.decode(token, @secret, true, algorithm: "HS256")
    {
      seller_id: payload["seller_id"].to_i,
      tg_user_id: payload["tg_user_id"].to_i
    }
  rescue JWT::DecodeError
    nil
  end
end
