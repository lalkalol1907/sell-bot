# frozen_string_literal: true

class WorkerLoginServiceClient
  def initialize(address)
    @stub = GrpcClients.worker_login_for(address)
    @metadata = GrpcClients.internal_metadata
  end

  def start_qr_login(owner_seller_id)
    req = Sellbot::Workerlogin::StartQRLoginRequest.new(owner_seller_id: owner_seller_id)
    @stub.start_qr_login(req, @metadata)
  end

  def start_phone_login(owner_seller_id, phone)
    req = Sellbot::Workerlogin::StartLoginRequest.new(owner_seller_id: owner_seller_id, phone: phone)
    @stub.start_login(req, @metadata)
  end

  def submit_code(login_id, code)
    req = Sellbot::Workerlogin::SubmitCodeRequest.new(login_id: login_id, code: code)
    @stub.submit_code(req, @metadata)
  end

  def submit_password(login_id, password)
    req = Sellbot::Workerlogin::SubmitPasswordRequest.new(login_id: login_id, password: password)
    @stub.submit_password(req, @metadata)
  end

  def get_status(login_id)
    req = Sellbot::Workerlogin::GetLoginStatusRequest.new(login_id: login_id)
    @stub.get_login_status(req, @metadata)
  end
end
