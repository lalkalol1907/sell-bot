# frozen_string_literal: true

require "rails_helper"

RSpec.describe TelegramInitDataAuth do
  let(:bot_token) { "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" }

  def build_init_data(user_id:, bot_token:)
    user = { id: user_id, first_name: "Test" }.to_json
    auth_date = Time.now.to_i.to_s
    params = { auth_date: auth_date, user: user }
    data_check_string = params.sort.map { |k, v| "#{k}=#{v}" }.join("\n")
    secret_key = OpenSSL::HMAC.digest("SHA256", "WebAppData", bot_token)
    hash = OpenSSL::HMAC.hexdigest("SHA256", secret_key, data_check_string)
    URI.encode_www_form(params.merge(hash: hash))
  end

  it "accepts valid init data" do
    init_data = build_init_data(user_id: 42, bot_token: bot_token)
    user = described_class.new(bot_token: bot_token).validate(init_data)
    expect(user[:id]).to eq(42)
  end

  it "rejects tampered hash" do
    init_data = build_init_data(user_id: 42, bot_token: bot_token) + "x"
    expect(described_class.new(bot_token: bot_token).validate(init_data)).to be_nil
  end
end
