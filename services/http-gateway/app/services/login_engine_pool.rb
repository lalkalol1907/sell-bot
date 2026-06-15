# frozen_string_literal: true

class LoginEnginePool
  def initialize(addresses: GatewayConfig.login_engine_addrs)
    @addresses = addresses
    @counter = 0
    @mutex = Mutex.new
  end

  def size
    @addresses.size
  end

  def pick_for_new_session(seed)
    @mutex.synchronize do
      addr = LoginRouting.pick_engine_address(@addresses, seed, @counter)
      @counter += 1
      addr
    end
  end
end
