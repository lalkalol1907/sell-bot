# frozen_string_literal: true

module Api
  module V1
    module Seller
      class StatsController < ApplicationController
        include SellerAuthenticatable

        def show
          stats = LeadsServiceClient.new.stats(current_seller_id, days: params.fetch(:days, 30).to_i)
          render json: {
            total: stats.total,
            new_count: stats.new_count,
            contacted: stats.contacted,
            closed: stats.closed,
            spam: stats.spam
          }
        end
      end
    end
  end
end
