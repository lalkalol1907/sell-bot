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
const loginProto = grpc.loadPackageDefinition(loadProto("worker_login.proto")) as any;

export type LoginStep = {
  login_id: string;
  status: string;
  message: string;
  worker_id: string;
  qr_url: string;
  qr_expires_at: string;
};

export type Seller = {
  id: string;
  tg_user_id: string;
};

function withToken(token: string): grpc.Metadata {
  const md = new grpc.Metadata();
  if (token) md.set(INTERNAL_GRPC_METADATA_KEY, token);
  return md;
}

export function createCatalogClient(address: string) {
  const Service = catalogProto.sellbot.catalog.CatalogService;
  return new Service(address, grpc.credentials.createInsecure());
}

export function createLoginClient(address: string) {
  const Service = loginProto.sellbot.workerlogin.WorkerLoginService;
  return new Service(address, grpc.credentials.createInsecure());
}

export async function getSellerByTgId(
  client: any,
  tgUserId: number,
): Promise<Seller | null> {
  return new Promise((resolve, reject) => {
    client.GetSellerByTgId({ tg_user_id: tgUserId }, (err: Error | null, res: Seller) => {
      if (err) {
        if ((err as grpc.ServiceError).code === grpc.status.NOT_FOUND) {
          resolve(null);
          return;
        }
        reject(err);
        return;
      }
      resolve(res);
    });
  });
}

function callLogin<T>(
  client: any,
  method: string,
  req: object,
  token: string,
): Promise<T> {
  const md = withToken(token);
  return new Promise((resolve, reject) => {
    client[method](req, md, (err: Error | null, res: T) => {
      if (err) reject(err);
      else resolve(res);
    });
  });
}

export function startQRLogin(client: any, sellerId: number, token: string): Promise<LoginStep> {
  return callLogin(client, "StartQRLogin", { owner_seller_id: sellerId }, token);
}

export function startPhoneLogin(
  client: any,
  sellerId: number,
  phone: string,
  token: string,
): Promise<LoginStep> {
  return callLogin(client, "StartLogin", { owner_seller_id: sellerId, phone }, token);
}

export function submitCode(
  client: any,
  loginId: string,
  code: string,
  token: string,
): Promise<LoginStep> {
  return callLogin(client, "SubmitCode", { login_id: loginId, code }, token);
}

export function submitPassword(
  client: any,
  loginId: string,
  password: string,
  token: string,
): Promise<LoginStep> {
  return callLogin(client, "SubmitPassword", { login_id: loginId, password }, token);
}

export function getLoginStatus(client: any, loginId: string, token: string): Promise<LoginStep> {
  return callLogin(client, "GetLoginStatus", { login_id: loginId }, token);
}
