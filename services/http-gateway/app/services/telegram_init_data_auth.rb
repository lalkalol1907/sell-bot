# frozen_string_literal: true

require "openssl"
require "json"

class TelegramInitDataAuth
  MAX_AGE_SEC = 86_400

  def initialize(bot_token: GatewayConfig.bot_token)
    @bot_token = bot_token
  end

  def validate(init_data)
    return nil if init_data.blank? || @bot_token.blank?

    params = URI.decode_www_form(init_data).to_h
    hash = params.delete("hash")
    return nil if hash.blank?

    data_check_string = params.sort.map { |k, v| "#{k}=#{v}" }.join("\n")
    secret_key = OpenSSL::HMAC.digest("SHA256", "WebAppData", @bot_token)
    computed = OpenSSL::HMAC.hexdigest("SHA256", secret_key, data_check_string)
    return nil unless ActiveSupport::SecurityUtils.secure_compare(computed, hash)

    auth_date = params["auth_date"].to_i
    return nil if auth_date.positive? && (Time.now.to_i - auth_date) > MAX_AGE_SEC

    user_raw = params["user"]
    return nil if user_raw.blank?

    user = JSON.parse(user_raw)
    return nil unless user.is_a?(Hash) && user["id"]

    {
      id: user["id"].to_i,
      first_name: user["first_name"],
      username: user["username"]
    }
  rescue JSON::ParserError
    nil
  end
end
