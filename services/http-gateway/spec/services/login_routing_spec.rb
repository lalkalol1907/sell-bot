# frozen_string_literal: true

require "rails_helper"

RSpec.describe LoginRouting do
  describe ".pick_engine_address" do
    it "round-robin pick uses all engines" do
      addrs = %w[a b c]
      picked = 10.times.map { |i| described_class.pick_engine_address(addrs, 0, i) }
      expect(picked.uniq.sort).to eq(addrs.sort)
    end
  end
end
