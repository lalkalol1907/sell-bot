# frozen_string_literal: true

module Api
  module V1
    module Login
      class SessionsController < ApplicationController
        include InitDataAuthenticatable

        before_action :resolve_seller_from_init_data!, except: []

        def session_check
          render json: { seller_id: @current_seller_id }
        end

        def qr_start
          step = start_on_engine { |client| client.start_qr_login(@current_seller_id) }
          render json: step_json(step)
        end

        def phone_start
          unless RateLimiter.new.allow?("phone:#{init_user[:id]}", limit: 5, window_ms: 60_000)
            return render json: { error: "rate limit exceeded" }, status: :too_many_requests
          end

          phone = phone_param
          return render json: { error: "invalid phone" }, status: :bad_request unless valid_phone?(phone)

          step = start_on_engine { |client| client.start_phone_login(@current_seller_id, phone) }
          render json: step_json(step)
        end

        def submit_code
          unless RateLimiter.new.allow?("code:#{init_user[:id]}", limit: 10, window_ms: 60_000)
            return render json: { error: "rate limit exceeded" }, status: :too_many_requests
          end

          code = params.require(:code).to_s.gsub(/\s+/, "")
          return render json: { error: "code required" }, status: :bad_request if code.blank?

          with_pinned_client do |client|
            step = client.submit_code(params[:login_id], code)
            clear_route_if_done(step, params[:login_id])
            render json: step_json(step)
          end
        end

        def submit_password
          password = params.require(:password).to_s
          return render json: { error: "password required" }, status: :bad_request if password.blank?

          with_pinned_client do |client|
            step = client.submit_password(params[:login_id], password)
            clear_route_if_done(step, params[:login_id])
            render json: step_json(step)
          end
        end

        def status
          with_pinned_client do |client|
            step = client.get_status(params[:login_id])
            clear_route_if_done(step, params[:login_id])
            render json: step_json(step)
          end
        end

        private

        def start_on_engine
          pool = LoginEnginePool.new
          engine_addr = pool.pick_for_new_session(@current_seller_id)
          client = WorkerLoginServiceClient.new(engine_addr)
          step = yield client
          LoginRouting.new.pin(step.login_id, engine_addr) if step.login_id.present?
          step
        end

        def with_pinned_client
          engine_addr = LoginRouting.new.resolve(params[:login_id])
          unless engine_addr
            return render json: { error: "login session expired, start again" }, status: :not_found
          end

          yield WorkerLoginServiceClient.new(engine_addr)
        end

        def clear_route_if_done(step, login_id)
          return unless %w[success error].include?(step.status)

          LoginRouting.new.clear(login_id)
        end

        def phone_param
          raw = params.require(:phone).to_s.strip
          raw.start_with?("+") ? raw : "+#{raw}"
        end

        def valid_phone?(phone)
          phone.match?(/^\+?\d{10,15}$/)
        end

        def step_json(step)
          {
            login_id: step.login_id,
            status: step.status,
            message: step.message,
            worker_id: step.worker_id.to_i,
            qr_url: step.qr_url.to_s,
            qr_expires_at: step.qr_expires_at.to_i
          }
        end
      end
    end
  end
end
