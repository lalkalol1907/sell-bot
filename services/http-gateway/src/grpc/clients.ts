import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import path from "node:path";

const PROTO_ROOT = path.resolve(import.meta.dir, "../../../proto");
const INTERNAL_GRPC_METADATA_KEY = "x-internal-grpc-token";

function loadProto(file: string) {
  return protoLoader.loadSync(path.join(PROTO_ROOT, file), {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
    includeDirs: [PROTO_ROOT],
  });
}

const catalogProto = grpc.loadPackageDefinition(loadProto("catalog.proto")) as any;
const leadsProto = grpc.loadPackageDefinition(loadProto("leads.proto")) as any;
const workersProto = grpc.loadPackageDefinition(loadProto("workers.proto")) as any;
const workerLoginProto = grpc.loadPackageDefinition(loadProto("worker_login.proto")) as any;

function promisify<T>(fn: (cb: (err: grpc.ServiceError | null, res: T) => void) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    fn((err, res) => (err ? reject(err) : resolve(res)));
  });
}

export type Seller = {
  id: number;
  tg_user_id: number;
  username: string;
  full_name: string;
  plan: string;
  sensitivity: string;
};

export type Product = {
  id: number;
  seller_id: number;
  title: string;
  price: string;
  currency: string;
  keywords: string[];
  is_active: boolean;
};

export type Lead = {
  id: number;
  seller_id: number;
  product_id: number;
  worker_id: number;
  chat_id: number;
  message_id: number;
  author_id: number;
  author_username: string;
  raw_text: string;
  matched_keywords: string[];
  product_score: number;
  intent_score: number;
  score: number;
  level: string;
  status: string;
};

export type Worker = {
  id: number;
  owner_seller_id: number;
  tg_account_id: number;
  phone: string;
  proxy: string;
  status: string;
};

export type LeadStats = {
  total: number;
  new_count: number;
  contacted: number;
  closed: number;
  spam: number;
};

export type LoginStep = {
  login_id: string;
  status: string;
  message: string;
  worker_id: number;
  qr_url: string;
  qr_expires_at: number;
};

function mapSeller(raw: any): Seller {
  return {
    id: Number(raw.id),
    tg_user_id: Number(raw.tg_user_id),
    username: raw.username ?? "",
    full_name: raw.full_name ?? "",
    plan: raw.plan ?? "",
    sensitivity: raw.sensitivity ?? "",
  };
}

function mapProduct(raw: any): Product {
  return {
    id: Number(raw.id),
    seller_id: Number(raw.seller_id),
    title: raw.title ?? "",
    price: String(raw.price ?? ""),
    currency: raw.currency ?? "",
    keywords: raw.keywords ?? [],
    is_active: Boolean(raw.is_active),
  };
}

function mapLead(raw: any): Lead {
  return {
    id: Number(raw.id),
    seller_id: Number(raw.seller_id),
    product_id: Number(raw.product_id),
    worker_id: Number(raw.worker_id),
    chat_id: Number(raw.chat_id),
    message_id: Number(raw.message_id),
    author_id: Number(raw.author_id),
    author_username: raw.author_username ?? "",
    raw_text: raw.raw_text ?? "",
    matched_keywords: raw.matched_keywords ?? [],
    product_score: Number(raw.product_score ?? 0),
    intent_score: Number(raw.intent_score ?? 0),
    score: Number(raw.score ?? 0),
    level: raw.level ?? "",
    status: raw.status ?? "",
  };
}

function mapWorker(raw: any): Worker {
  return {
    id: Number(raw.id),
    owner_seller_id: Number(raw.owner_seller_id),
    tg_account_id: Number(raw.tg_account_id ?? 0),
    phone: raw.phone ?? "",
    proxy: raw.proxy ?? "",
    status: raw.status ?? "",
  };
}

function mapLoginStep(raw: any): LoginStep {
  return {
    login_id: raw.login_id ?? "",
    status: raw.status ?? "",
    message: raw.message ?? "",
    worker_id: Number(raw.worker_id ?? 0),
    qr_url: raw.qr_url ?? "",
    qr_expires_at: Number(raw.qr_expires_at ?? 0),
  };
}

export class GrpcClients {
  private catalog: any;
  private leads: any;
  private workers: any;

  constructor(
    coreAddr: string,
    private internalToken: string,
  ) {
    this.catalog = new catalogProto.sellbot.catalog.CatalogService(
      coreAddr,
      grpc.credentials.createInsecure(),
    );
    this.leads = new leadsProto.sellbot.leads.LeadsService(
      coreAddr,
      grpc.credentials.createInsecure(),
    );
    this.workers = new workersProto.sellbot.workers.WorkersService(
      coreAddr,
      grpc.credentials.createInsecure(),
    );
  }

  private internalMetadata(): grpc.Metadata {
    const md = new grpc.Metadata();
    if (this.internalToken) {
      md.set(INTERNAL_GRPC_METADATA_KEY, this.internalToken);
    }
    return md;
  }

  async getSellerByTgId(tgUserId: number): Promise<Seller | null> {
    try {
      const res = await promisify<any>((cb) =>
        this.catalog.GetSellerByTgId({ tg_user_id: tgUserId }, cb),
      );
      return mapSeller(res);
    } catch (err: any) {
      if (err?.code === grpc.status.NOT_FOUND) return null;
      throw err;
    }
  }

  async getSeller(id: number): Promise<Seller> {
    const res = await promisify<any>((cb) => this.catalog.GetSeller({ id }, cb));
    return mapSeller(res);
  }

  async updateSeller(id: number, sensitivity: string): Promise<Seller> {
    const res = await promisify<any>((cb) =>
      this.catalog.UpdateSeller({ id, sensitivity }, cb),
    );
    return mapSeller(res);
  }

  async listProducts(sellerId: number, activeOnly = false): Promise<Product[]> {
    const res = await promisify<any>((cb) =>
      this.catalog.ListProducts({ seller_id: sellerId, active_only: activeOnly }, cb),
    );
    return (res.products ?? []).map(mapProduct);
  }

  async createProduct(input: {
    seller_id: number;
    title: string;
    price: string;
    currency: string;
    keywords: string[];
  }): Promise<Product> {
    const res = await promisify<any>((cb) => this.catalog.CreateProduct(input, cb));
    return mapProduct(res);
  }

  async updateProduct(input: {
    id: number;
    seller_id: number;
    title: string;
    price: string;
    currency: string;
    keywords: string[];
    is_active: boolean;
  }): Promise<Product> {
    const res = await promisify<any>((cb) => this.catalog.UpdateProduct(input, cb));
    return mapProduct(res);
  }

  async deleteProduct(id: number, sellerId: number): Promise<boolean> {
    const res = await promisify<any>((cb) =>
      this.catalog.DeleteProduct({ id, seller_id: sellerId }, cb),
    );
    return Boolean(res.success);
  }

  async listLeads(
    sellerId: number,
    status = "",
    limit = 50,
    offset = 0,
  ): Promise<{ leads: Lead[]; total: number }> {
    const res = await promisify<any>((cb) =>
      this.leads.ListLeads({ seller_id: sellerId, status, limit, offset }, cb),
    );
    return {
      leads: (res.leads ?? []).map(mapLead),
      total: Number(res.total ?? 0),
    };
  }

  async updateLeadStatus(id: number, sellerId: number, status: string): Promise<Lead> {
    const res = await promisify<any>((cb) =>
      this.leads.UpdateLeadStatus({ id, seller_id: sellerId, status }, cb),
    );
    return mapLead(res);
  }

  async getLeadStats(sellerId: number, days = 30): Promise<LeadStats> {
    const res = await promisify<any>((cb) =>
      this.leads.GetLeadStats({ seller_id: sellerId, days }, cb),
    );
    return {
      total: Number(res.total ?? 0),
      new_count: Number(res.new_count ?? 0),
      contacted: Number(res.contacted ?? 0),
      closed: Number(res.closed ?? 0),
      spam: Number(res.spam ?? 0),
    };
  }

  async listWorkers(ownerSellerId: number): Promise<Worker[]> {
    const res = await promisify<any>((cb) =>
      this.workers.ListWorkers({ owner_seller_id: ownerSellerId }, cb),
    );
    return (res.workers ?? []).map(mapWorker);
  }

  async updateWorkerStatus(id: number, status: string): Promise<Worker> {
    const res = await promisify<any>((cb) =>
      this.workers.UpdateWorkerStatus({ id, status }, cb),
    );
    return mapWorker(res);
  }

  createWorkerLoginClient(address: string) {
    return new workerLoginProto.sellbot.workerlogin.WorkerLoginService(
      address,
      grpc.credentials.createInsecure(),
    );
  }

  async startQrLogin(client: any, ownerSellerId: number): Promise<LoginStep> {
    const res = await promisify<any>((cb) =>
      client.StartQRLogin({ owner_seller_id: ownerSellerId }, this.internalMetadata(), cb),
    );
    return mapLoginStep(res);
  }

  async startPhoneLogin(client: any, ownerSellerId: number, phone: string): Promise<LoginStep> {
    const res = await promisify<any>((cb) =>
      client.StartLogin({ owner_seller_id: ownerSellerId, phone }, this.internalMetadata(), cb),
    );
    return mapLoginStep(res);
  }

  async submitCode(client: any, loginId: string, code: string): Promise<LoginStep> {
    const res = await promisify<any>((cb) =>
      client.SubmitCode({ login_id: loginId, code }, this.internalMetadata(), cb),
    );
    return mapLoginStep(res);
  }

  async submitPassword(client: any, loginId: string, password: string): Promise<LoginStep> {
    const res = await promisify<any>((cb) =>
      client.SubmitPassword({ login_id: loginId, password }, this.internalMetadata(), cb),
    );
    return mapLoginStep(res);
  }

  async getLoginStatus(client: any, loginId: string): Promise<LoginStep> {
    const res = await promisify<any>((cb) =>
      client.GetLoginStatus({ login_id: loginId }, this.internalMetadata(), cb),
    );
    return mapLoginStep(res);
  }
}

export function grpcErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "details" in err && typeof (err as any).details === "string") {
    return (err as any).details;
  }
  if (err instanceof Error) return err.message;
  return "request failed";
}
