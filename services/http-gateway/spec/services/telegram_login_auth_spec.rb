# frozen_string_literal: true

require "rails_helper"

RSpec.describe TelegramLoginAuth do
  let(:bot_token) { "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" }

  def build_widget_params(user_id:)
    auth_date = Time.now.to_i
    params = {
      id: user_id,
      first_name: "Test",
      auth_date: auth_date
    }
    data_check_string = params.sort.map { |k, v| "#{k}=#{v}" }.join("\n")
    secret_key = Digest::SHA256.digest(bot_token)
    hash = OpenSSL::HMAC.hexdigest("SHA256", secret_key, data_check_string)
    params.merge(hash: hash)
  end

  it "accepts valid login widget payload" do
    payload = build_widget_params(user_id: 99)
    user = described_class.new(bot_token: bot_token).validate(payload)
    expect(user[:id]).to eq(99)
  end
end
