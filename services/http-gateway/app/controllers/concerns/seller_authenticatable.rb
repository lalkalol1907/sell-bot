# frozen_string_literal: true

module SellerAuthenticatable
  extend ActiveSupport::Concern

  included do
    before_action :authenticate_seller!
  end

  private

  def authenticate_seller!
    token = cookies[JwtSession::COOKIE_NAME]
    session = JwtSession.new.decode(token)
    unless session && session[:seller_id].positive?
      render json: { error: "unauthorized" }, status: :unauthorized
      return
    end

    @current_seller_id = session[:seller_id]
    @current_tg_user_id = session[:tg_user_id]
  end

  def current_seller_id
    @current_seller_id
  end
end
