# frozen_string_literal: true

module Api
  module V1
    class AuthController < ApplicationController
      def telegram
        user = TelegramLoginAuth.new.validate(auth_params)
        return render json: { error: "invalid telegram auth" }, status: :unauthorized unless user

        seller = CatalogServiceClient.new.get_seller_by_tg_id(user[:id])
        unless seller&.id&.positive?
          return render json: { error: "seller not found, run /start in bot first" }, status: :unauthorized
        end

        token = JwtSession.new.encode(seller_id: seller.id, tg_user_id: user[:id])
        cookies[JwtSession::COOKIE_NAME] = {
          value: token,
          httponly: true,
          secure: Rails.env.production?,
          same_site: :lax,
          path: "/"
        }

        render json: seller_json(seller)
      end

      def logout
        cookies.delete(JwtSession::COOKIE_NAME, path: "/")
        head :no_content
      end

      def me
        token = cookies[JwtSession::COOKIE_NAME]
        session = JwtSession.new.decode(token)
        return render json: { error: "unauthorized" }, status: :unauthorized unless session

        seller = CatalogServiceClient.new.get_seller(session[:seller_id])
        render json: seller_json(seller)
      rescue GRPC::NotFound
        render json: { error: "unauthorized" }, status: :unauthorized
      end

      private

      def auth_params
        params.permit(:id, :first_name, :last_name, :username, :photo_url, :auth_date, :hash)
      end

      def seller_json(seller)
        {
          id: seller.id,
          tg_user_id: seller.tg_user_id,
          username: seller.username,
          full_name: seller.full_name,
          sensitivity: seller.sensitivity,
          plan: seller.plan
        }
      end
    end
  end
end
