# frozen_string_literal: true

require "openssl"
require "digest"

class TelegramLoginAuth
  MAX_AGE_SEC = 86_400

  def initialize(bot_token: GatewayConfig.bot_token)
    @bot_token = bot_token
  end

  # Validates Telegram Login Widget callback payload.
  def validate(params)
    return nil if @bot_token.blank?

    data = params.to_h.stringify_keys
    hash = data.delete("hash")
    return nil if hash.blank?

    data_check_string = data.sort.map { |k, v| "#{k}=#{v}" }.join("\n")
    secret_key = Digest::SHA256.digest(@bot_token)
    computed = OpenSSL::HMAC.hexdigest("SHA256", secret_key, data_check_string)
    return nil unless ActiveSupport::SecurityUtils.secure_compare(computed, hash)

    auth_date = data["auth_date"].to_i
    return nil if auth_date.positive? && (Time.now.to_i - auth_date) > MAX_AGE_SEC

    id = data["id"].to_i
    return nil unless id.positive?

    {
      id: id,
      first_name: data["first_name"],
      username: data["username"]
    }
  end
end
