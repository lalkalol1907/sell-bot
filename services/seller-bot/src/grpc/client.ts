import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import path from "node:path";

const PROTO_ROOT = path.resolve(import.meta.dir, "../../../proto");

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

export type Seller = {
  id: string;
  tg_user_id: string;
  username: string;
  full_name: string;
  sensitivity: string;
};

export type Product = {
  id: string;
  title: string;
  price: string;
  currency: string;
  is_active: boolean;
  keywords?: string[];
};

export type Lead = {
  id: string;
  raw_text: string;
  level: string;
  status: string;
  product_id: string;
};

export type Worker = {
  id: string;
  phone: string;
  status: string;
};

export type MonitoredChat = {
  id: string;
  chat_id: string;
  title: string;
  is_active: boolean;
};

function promisify<T>(fn: (cb: (err: Error | null, res: T) => void) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    fn((err, res) => (err ? reject(err) : resolve(res)));
  });
}

export function createCatalogClient(address: string) {
  const Service = catalogProto.sellbot.catalog.CatalogService;
  return new Service(address, grpc.credentials.createInsecure());
}

export function createLeadsClient(address: string) {
  const Service = leadsProto.sellbot.leads.LeadsService;
  return new Service(address, grpc.credentials.createInsecure());
}

export function createWorkersClient(address: string) {
  const Service = workersProto.sellbot.workers.WorkersService;
  return new Service(address, grpc.credentials.createInsecure());
}

export function createSeller(
  client: any,
  tgUserId: number,
  username: string,
  fullName: string,
): Promise<Seller> {
  return promisify((cb) =>
    client.CreateSeller({ tg_user_id: tgUserId, username, full_name: fullName }, cb),
  );
}

export function createProduct(
  client: any,
  sellerId: number,
  title: string,
  price: string,
  currency: string,
  keywords: string[],
): Promise<unknown> {
  return promisify((cb) =>
    client.CreateProduct({ seller_id: sellerId, title, price, currency, keywords }, cb),
  );
}

export function listProducts(client: any, sellerId: number): Promise<Product[]> {
  return promisify<{ products: Product[] }>((cb) =>
    client.ListProducts({ seller_id: sellerId, active_only: false }, cb),
  ).then((r) => r.products ?? []);
}

export function getSeller(client: any, sellerId: number): Promise<Seller> {
  return promisify((cb) => client.GetSeller({ id: sellerId }, cb));
}

export function updateSeller(client: any, sellerId: number, sensitivity: string): Promise<Seller> {
  return promisify((cb) => client.UpdateSeller({ id: sellerId, sensitivity }, cb));
}

export function updateProduct(
  client: any,
  input: {
    id: number;
    seller_id: number;
    title: string;
    price: string;
    currency: string;
    keywords: string[];
    is_active: boolean;
  },
): Promise<Product> {
  return promisify((cb) => client.UpdateProduct(input, cb));
}

export function deleteProduct(client: any, productId: number, sellerId: number): Promise<boolean> {
  return promisify<{ success: boolean }>((cb) =>
    client.DeleteProduct({ id: productId, seller_id: sellerId }, cb),
  ).then((r) => r.success ?? false);
}

export function toggleProduct(
  client: any,
  product: Product,
  sellerId: number,
): Promise<Product> {
  return updateProduct(client, {
    id: Number(product.id),
    seller_id: sellerId,
    title: product.title,
    price: product.price,
    currency: product.currency,
    keywords: product.keywords ?? [],
    is_active: !product.is_active,
  });
}

export function updateLeadStatus(
  client: any,
  leadId: number,
  sellerId: number,
  status: string,
): Promise<void> {
  return promisify((cb) => client.UpdateLeadStatus({ id: leadId, seller_id: sellerId, status }, cb));
}

export function listLeads(client: any, sellerId: number, limit = 10): Promise<Lead[]> {
  return promisify<{ leads: Lead[] }>((cb) =>
    client.ListLeads({ seller_id: sellerId, status: "", limit, offset: 0 }, cb),
  ).then((r) => r.leads ?? []);
}

export function getLeadStats(client: any, sellerId: number, days = 30): Promise<{
  total: number;
  new_count: number;
  contacted: number;
  closed: number;
  spam: number;
}> {
  return promisify((cb) => client.GetLeadStats({ seller_id: sellerId, days }, cb));
}

export function listWorkers(client: any, sellerId: number): Promise<Worker[]> {
  return promisify<{ workers: Worker[] }>((cb) =>
    client.ListWorkers({ owner_seller_id: sellerId }, cb),
  ).then((r) => r.workers ?? []);
}

export function listChats(client: any, workerId: number, sellerId: number): Promise<MonitoredChat[]> {
  return promisify<{ chats: MonitoredChat[] }>((cb) =>
    client.ListChats({ worker_id: workerId, owner_seller_id: sellerId }, cb),
  ).then((r) => r.chats ?? []);
}

export function setChatWhitelist(
  client: any,
  workerId: number,
  sellerId: number,
  entries: { chat_id: number; is_active: boolean }[],
): Promise<number> {
  return promisify<{ updated: number }>((cb) =>
    client.SetChatWhitelist({ worker_id: workerId, owner_seller_id: sellerId, entries }, cb),
  ).then((r) => r.updated ?? 0);
}

export type LoginStep = {
  login_id: string;
  status: string;
  message: string;
  worker_id: string;
};

export function createWorkerLoginClient(address: string) {
  const loginProto = grpc.loadPackageDefinition(loadProto("worker_login.proto")) as any;
  const Service = loginProto.sellbot.workerlogin.WorkerLoginService;
  return new Service(address, grpc.credentials.createInsecure());
}

const INTERNAL_GRPC_METADATA_KEY = "x-internal-grpc-token";

export function startWorkerLogin(
  client: any,
  ownerSellerId: number,
  phone: string,
  internalToken = "",
): Promise<LoginStep> {
  const metadata = new grpc.Metadata();
  if (internalToken) {
    metadata.set(INTERNAL_GRPC_METADATA_KEY, internalToken);
  }
  return promisify((cb) =>
    client.StartLogin({ owner_seller_id: ownerSellerId, phone }, metadata, cb),
  );
}

export function submitWorkerLoginCode(client: any, loginId: string, code: string): Promise<LoginStep> {
  return promisify((cb) => client.SubmitCode({ login_id: loginId, code }, cb));
}

export function submitWorkerLoginPassword(
  client: any,
  loginId: string,
  password: string,
): Promise<LoginStep> {
  return promisify((cb) => client.SubmitPassword({ login_id: loginId, password }, cb));
}
