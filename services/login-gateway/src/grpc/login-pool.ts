import { createLoginClient } from "./client.js";
import { pickEngineAddress } from "../login-routing.js";

export class LoginEnginePool {
  private readonly clients = new Map<string, ReturnType<typeof createLoginClient>>();
  private counter = 0;

  constructor(private readonly addresses: readonly string[]) {
    if (addresses.length === 0) {
      throw new Error("login engine pool requires at least one address");
    }
  }

  get size() {
    return this.addresses.length;
  }

  pickForNewSession(seed: number): string {
    const address = pickEngineAddress(this.addresses, seed, this.counter);
    this.counter += 1;
    return address;
  }

  clientFor(address: string) {
    let client = this.clients.get(address);
    if (!client) {
      client = createLoginClient(address);
      this.clients.set(address, client);
    }
    return client;
  }
}
