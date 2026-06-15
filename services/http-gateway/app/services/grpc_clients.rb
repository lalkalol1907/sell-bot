# frozen_string_literal: true

module GrpcClients
  INTERNAL_METADATA_KEY = "x-internal-grpc-token"

  module_function

  def catalog
    @catalog ||= Sellbot::Catalog::CatalogService::Stub.new(
      GatewayConfig.core_grpc_addr,
      :this_channel_is_insecure
    )
  end

  def leads
    @leads ||= Sellbot::Leads::LeadsService::Stub.new(
      GatewayConfig.core_grpc_addr,
      :this_channel_is_insecure
    )
  end

  def workers
    @workers ||= Sellbot::Workers::WorkersService::Stub.new(
      GatewayConfig.core_grpc_addr,
      :this_channel_is_insecure
    )
  end

  def worker_login_for(address)
    Sellbot::Workerlogin::WorkerLoginService::Stub.new(address, :this_channel_is_insecure)
  end

  def internal_metadata
    md = {}
    token = GatewayConfig.internal_grpc_token
    md[INTERNAL_METADATA_KEY] = token if token.present?
    md
  end
end
