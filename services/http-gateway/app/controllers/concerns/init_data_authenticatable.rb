# frozen_string_literal: true

module InitDataAuthenticatable
  extend ActiveSupport::Concern

  private

  def authenticate_init_data!
    init_data = request.headers["X-Telegram-Init-Data"].presence ||
                request.headers["HTTP_X_TELEGRAM_INIT_DATA"].presence
    @init_user = TelegramInitDataAuth.new.validate(init_data)
    return if @init_user

    render json: { error: "invalid init data" }, status: :unauthorized
  end

  def resolve_seller_from_init_data!
    authenticate_init_data!
    return if performed?

    seller = CatalogServiceClient.new.get_seller_by_tg_id(@init_user[:id])
    unless seller&.id&.positive?
      render json: { error: "seller not found, run /start in bot first" }, status: :unauthorized
      return
    end

    @current_seller_id = seller.id
  end

  def init_user
    @init_user
  end
end
