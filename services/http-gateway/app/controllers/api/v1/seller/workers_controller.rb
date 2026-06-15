# frozen_string_literal: true

module Api
  module V1
    module Seller
      class WorkersController < ApplicationController
        include SellerAuthenticatable

        def index
          workers = WorkersServiceClient.new.list_workers(current_seller_id)
          render json: { workers: workers.map { |w| worker_json(w) } }
        end

        def update_status
          worker = WorkersServiceClient.new.update_status(params[:id].to_i, status_params[:status])
          render json: worker_json(worker)
        rescue GRPC::BadStatus => e
          render json: { error: e.details || "invalid worker" }, status: :bad_request
        end

        private

        def status_params
          params.require(:worker).permit(:status)
        end

        def worker_json(worker)
          {
            id: worker.id,
            owner_seller_id: worker.owner_seller_id,
            tg_account_id: worker.tg_account_id,
            phone: worker.phone,
            proxy: worker.proxy,
            status: worker.status
          }
        end
      end
    end
  end
end
