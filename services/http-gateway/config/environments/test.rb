# frozen_string_literal: true

require "active_support/core_ext/integer/time"

Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = true
  config.consider_all_requests_local = false
  config.public_file_server.enabled = false
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "warn")
  config.i18n.fallbacks = true
  config.active_support.report_deprecations = false
end
