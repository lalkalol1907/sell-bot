# frozen_string_literal: true

class WorkersServiceClient
  def list_workers(owner_seller_id)
    req = Sellbot::Workers::ListWorkersRequest.new(owner_seller_id: owner_seller_id)
    GrpcClients.workers.list_workers(req).workers
  end

  def update_status(id, status)
    req = Sellbot::Workers::UpdateWorkerStatusRequest.new(id: id, status: status)
    GrpcClients.workers.update_worker_status(req)
  end
end
