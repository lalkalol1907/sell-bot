# frozen_string_literal: true

module Api
  module V1
    module Seller
      class SettingsController < ApplicationController
        include SellerAuthenticatable

        def update
          seller = CatalogServiceClient.new.update_seller(
            current_seller_id,
            sensitivity: settings_params[:sensitivity]
          )
          render json: {
            id: seller.id,
            sensitivity: seller.sensitivity
          }
        rescue GRPC::BadStatus => e
          render json: { error: e.details || "invalid settings" }, status: :bad_request
        end

        private

        def settings_params
          params.require(:settings).permit(:sensitivity)
        end
      end
    end
  end
end
