# frozen_string_literal: true

Rails.application.routes.draw do
  get "/health", to: "health#show"
  get "/metrics", to: "health#metrics"

  namespace :api do
    namespace :v1 do
      post "auth/telegram", to: "auth#telegram"
      post "auth/logout", to: "auth#logout"
      get "auth/me", to: "auth#me"

      namespace :seller do
        resources :products, only: %i[index create update destroy]
        resources :leads, only: %i[index update]
        resources :workers, only: %i[index] do
          member do
            patch :status, action: :update_status
          end
        end
        get :stats, to: "stats#show"
        patch :settings, to: "settings#update"
      end

      post "login/session", to: "login/sessions#session_check"
      post "login/qr/start", to: "login/sessions#qr_start"
      post "login/phone/start", to: "login/sessions#phone_start"
      post "login/:login_id/code", to: "login/sessions#submit_code"
      post "login/:login_id/password", to: "login/sessions#submit_password"
      get "login/:login_id/status", to: "login/sessions#status"
    end
  end
end
