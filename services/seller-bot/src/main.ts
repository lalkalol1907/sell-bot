import { createBot } from "./index.js";

const token = process.env.BOT_TOKEN;
if (!token) {
  console.error("BOT_TOKEN is required");
  process.exit(1);
}

const coreAddr = process.env.CORE_GRPC_ADDR ?? "core:50051";
const natsUrl = process.env.NATS_URL ?? "nats://nats:4222";
const redisUrl = process.env.REDIS_URL ?? "redis://redis:6379/0";

const workerLoginAddr = process.env.WORKER_LOGIN_GRPC_ADDR ?? "worker-engine:50053";
const internalGrpcToken = process.env.INTERNAL_GRPC_TOKEN ?? "";

const bot = await createBot(token, coreAddr, natsUrl, redisUrl, workerLoginAddr, internalGrpcToken);
console.log("seller-bot starting...");
bot.start();
