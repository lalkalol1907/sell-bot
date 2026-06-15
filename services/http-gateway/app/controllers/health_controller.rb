# frozen_string_literal: true

class HealthController < ApplicationController
  def show
    render json: {
      status: "ok",
      login_engines: GatewayConfig.login_engine_addrs.size
    }
  end

  def metrics
    render plain: "# HELP http_gateway_up HTTP gateway is running\n# TYPE http_gateway_up gauge\nhttp_gateway_up 1\n",
           content_type: "text/plain; version=0.0.4"
  end
end
