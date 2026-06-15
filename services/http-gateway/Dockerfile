FROM ruby:3.3-slim AS base
WORKDIR /build

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    build-essential curl protobuf-compiler libyaml-dev git && \
    rm -rf /var/lib/apt/lists/*

COPY proto /build/proto
COPY scripts/gen-proto-ruby.sh /build/scripts/gen-proto-ruby.sh
COPY services/http-gateway/Gemfile services/http-gateway/Gemfile.lock* /build/services/http-gateway/

WORKDIR /build/services/http-gateway
RUN bundle install

RUN chmod +x /build/scripts/gen-proto-ruby.sh && /build/scripts/gen-proto-ruby.sh

COPY services/http-gateway/ /build/services/http-gateway/

ENV RAILS_ENV=production
ENV PORT=3000
WORKDIR /build/services/http-gateway
EXPOSE 3000

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
