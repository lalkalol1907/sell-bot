import {
  AckPolicy,
  connect,
  DeliverPolicy,
  StringCodec,
  type JetStreamManager,
  type NatsConnection,
} from "nats";
import type { Bot } from "grammy";
import type { BotContext } from "../types.js";
import { incWorkerAlerts } from "../metrics.js";

const sc = StringCodec();
const STREAM_NAME = "SELLBOT";
const CONSUMER_NAME = "seller-bot-worker-status";
const QUEUE_GROUP = "seller-bot-worker-status";
const SUBJECT = "worker.status";

export type WorkerStatusEvent = {
  worker_id: number;
  owner_seller_id: number;
  status: string;
  phone?: string;
};

const STATUS_MESSAGES: Record<string, string> = {
  auth_required: "⚠️ Воркер #{id} требует повторной авторизации. Лиды из его чатов не поступают.",
  banned: "🚫 Воркер #{id} заблокирован Telegram.",
  error: "❌ Воркер #{id} остановлен из-за ошибки.",
};

async function ensureConsumer(jsm: JetStreamManager) {
  try {
    await jsm.consumers.info(STREAM_NAME, CONSUMER_NAME);
  } catch {
    await jsm.consumers.add(STREAM_NAME, {
      durable_name: CONSUMER_NAME,
      deliver_group: QUEUE_GROUP,
      filter_subject: SUBJECT,
      deliver_policy: DeliverPolicy.All,
      ack_policy: AckPolicy.Explicit,
      max_deliver: 5,
    });
  }
}

export async function subscribeWorkerStatus(
  bot: Bot<BotContext>,
  natsUrl: string,
  resolveSellerTgId: (sellerId: number) => Promise<number | null>,
): Promise<NatsConnection> {
  const nc = await connect({ servers: natsUrl });
  const jsm = await nc.jetstreamManager();
  await ensureConsumer(jsm);

  const js = nc.jetstream();
  const consumer = await js.consumers.get(STREAM_NAME, CONSUMER_NAME);
  const messages = await consumer.consume();

  (async () => {
    for await (const msg of messages) {
      try {
        const event = JSON.parse(sc.decode(msg.data)) as WorkerStatusEvent;
        const tgUserId = await resolveSellerTgId(event.owner_seller_id);
        if (!tgUserId) {
          msg.ack();
          continue;
        }

        const template = STATUS_MESSAGES[event.status] ?? "Воркер #{id}: статус {status}";
        const text = template
          .replace("#{id}", String(event.worker_id))
          .replace("{status}", event.status);

        await bot.api.sendMessage(tgUserId, text);
        incWorkerAlerts();
        msg.ack();
      } catch (err) {
        console.error("failed to handle worker.status", err);
        msg.nak();
      }
    }
  })();

  return nc;
}
