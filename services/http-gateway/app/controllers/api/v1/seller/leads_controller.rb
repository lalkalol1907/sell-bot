# frozen_string_literal: true

module Api
  module V1
    module Seller
      class LeadsController < ApplicationController
        include SellerAuthenticatable

        def index
          resp = LeadsServiceClient.new.list_leads(
            current_seller_id,
            status: params[:status].to_s,
            limit: params.fetch(:limit, 50).to_i,
            offset: params.fetch(:offset, 0).to_i
          )
          render json: {
            leads: resp.leads.map { |l| lead_json(l) },
            total: resp.total
          }
        end

        def update
          lead = LeadsServiceClient.new.update_status(
            params[:id].to_i,
            current_seller_id,
            lead_params[:status]
          )
          render json: lead_json(lead)
        rescue GRPC::BadStatus => e
          render json: { error: e.details || "invalid lead" }, status: :bad_request
        end

        private

        def lead_params
          params.require(:lead).permit(:status)
        end

        def lead_json(lead)
          {
            id: lead.id,
            seller_id: lead.seller_id,
            product_id: lead.product_id,
            worker_id: lead.worker_id,
            chat_id: lead.chat_id,
            message_id: lead.message_id,
            author_id: lead.author_id,
            author_username: lead.author_username,
            raw_text: lead.raw_text,
            matched_keywords: lead.matched_keywords.to_a,
            product_score: lead.product_score,
            intent_score: lead.intent_score,
            score: lead.score,
            level: lead.level,
            status: lead.status
          }
        end
      end
    end
  end
end
