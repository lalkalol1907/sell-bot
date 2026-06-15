# frozen_string_literal: true

module Api
  module V1
    module Seller
      class ProductsController < ApplicationController
        include SellerAuthenticatable

        def index
          products = CatalogServiceClient.new.list_products(current_seller_id)
          render json: { products: products.map { |p| product_json(p) } }
        end

        def create
          product = CatalogServiceClient.new.create_product(
            seller_id: current_seller_id,
            title: product_params[:title],
            price: product_params[:price],
            currency: product_params[:currency],
            keywords: product_params[:keywords] || []
          )
          render json: product_json(product), status: :created
        rescue GRPC::BadStatus => e
          render json: { error: e.details || "invalid product" }, status: :bad_request
        end

        def update
          product = CatalogServiceClient.new.update_product(
            id: params[:id].to_i,
            seller_id: current_seller_id,
            title: product_params[:title],
            price: product_params[:price],
            currency: product_params[:currency],
            keywords: product_params[:keywords] || [],
            is_active: product_params.key?(:is_active) ? product_params[:is_active] : true
          )
          render json: product_json(product)
        rescue GRPC::BadStatus => e
          render json: { error: e.details || "invalid product" }, status: :bad_request
        end

        def destroy
          ok = CatalogServiceClient.new.delete_product(params[:id].to_i, current_seller_id)
          render json: { success: ok }
        end

        private

        def product_params
          params.require(:product).permit(:title, :price, :currency, :is_active, keywords: [])
        end

        def product_json(product)
          {
            id: product.id,
            seller_id: product.seller_id,
            title: product.title,
            price: product.price,
            currency: product.currency,
            keywords: product.keywords.to_a,
            is_active: product.is_active
          }
        end
      end
    end
  end
end
