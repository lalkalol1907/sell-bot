# frozen_string_literal: true

class LeadsServiceClient
  def list_leads(seller_id, status: "", limit: 50, offset: 0)
    req = Sellbot::Leads::ListLeadsRequest.new(
      seller_id: seller_id,
      status: status.to_s,
      limit: limit,
      offset: offset
    )
    GrpcClients.leads.list_leads(req)
  end

  def update_status(id, seller_id, status)
    req = Sellbot::Leads::UpdateLeadStatusRequest.new(id: id, seller_id: seller_id, status: status)
    GrpcClients.leads.update_lead_status(req)
  end

  def stats(seller_id, days: 30)
    req = Sellbot::Leads::GetLeadStatsRequest.new(seller_id: seller_id, days: days)
    GrpcClients.leads.get_lead_stats(req)
  end
end
