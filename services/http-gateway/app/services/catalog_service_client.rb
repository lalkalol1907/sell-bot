# frozen_string_literal: true

class CatalogServiceClient
  def get_seller_by_tg_id(tg_user_id)
    req = Sellbot::Catalog::GetSellerByTgIdRequest.new(tg_user_id: tg_user_id)
    GrpcClients.catalog.get_seller_by_tg_id(req)
  rescue GRPC::NotFound
    nil
  end

  def get_seller(id)
    req = Sellbot::Catalog::GetSellerRequest.new(id: id)
    GrpcClients.catalog.get_seller(req)
  end

  def update_seller(id, sensitivity:)
    req = Sellbot::Catalog::UpdateSellerRequest.new(id: id, sensitivity: sensitivity)
    GrpcClients.catalog.update_seller(req)
  end

  def list_products(seller_id, active_only: false)
    req = Sellbot::Catalog::ListProductsRequest.new(seller_id: seller_id, active_only: active_only)
    GrpcClients.catalog.list_products(req).products
  end

  def create_product(seller_id:, title:, price:, currency:, keywords:)
    req = Sellbot::Catalog::CreateProductRequest.new(
      seller_id: seller_id,
      title: title,
      price: price,
      currency: currency,
      keywords: keywords
    )
    GrpcClients.catalog.create_product(req)
  end

  def update_product(id:, seller_id:, title:, price:, currency:, keywords:, is_active:)
    req = Sellbot::Catalog::UpdateProductRequest.new(
      id: id,
      seller_id: seller_id,
      title: title,
      price: price,
      currency: currency,
      keywords: keywords,
      is_active: is_active
    )
    GrpcClients.catalog.update_product(req)
  end

  def delete_product(id, seller_id)
    req = Sellbot::Catalog::DeleteProductRequest.new(id: id, seller_id: seller_id)
    GrpcClients.catalog.delete_product(req).success
  end
end
