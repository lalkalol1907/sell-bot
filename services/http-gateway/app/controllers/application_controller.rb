# frozen_string_literal: true

class ApplicationController < ActionController::API
  include ActionController::Cookies

  rescue_from StandardError, with: :internal_error

  private

  def internal_error(error)
    Rails.logger.error("#{error.class}: #{error.message}\n#{error.backtrace&.first(5)&.join("\n")}")
    render json: { error: "internal error" }, status: :internal_server_error
  end
end
