import { InlineKeyboard } from "grammy";
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
import { formatLeadNotification, type LeadCreatedEvent } from "../utils/lead-notification.js";
import { incLeadsDelivered } from "../metrics.js";

const sc = StringCodec();
const STREAM_NAME = "SELLBOT";
const CONSUMER_NAME = "seller-bot-leads";
const SUBJECT = "lead.created";

function leadKeyboard(leadId: number) {
  return new InlineKeyboard()
    .text("В работе", `lead:contacted:${leadId}`)
    .text("Закрыть", `lead:closed:${leadId}`)
    .row()
    .text("Спам", `lead:spam:${leadId}`);
}

async function ensureStream(jsm: JetStreamManager) {
  try {
    await jsm.streams.info(STREAM_NAME);
  } catch {
    await jsm.streams.add({
      name: STREAM_NAME,
      subjects: ["lead.created", "worker.status", "message.captured"],
    });
  }
}

async function ensureConsumer(jsm: JetStreamManager) {
  try {
    await jsm.consumers.info(STREAM_NAME, CONSUMER_NAME);
  } catch {
    await jsm.consumers.add(STREAM_NAME, {
      durable_name: CONSUMER_NAME,
      filter_subject: SUBJECT,
      deliver_policy: DeliverPolicy.All,
      ack_policy: AckPolicy.Explicit,
      max_deliver: 5,
    });
  }
}

export async function subscribeLeadCreated(bot: Bot<BotContext>, natsUrl: string): Promise<NatsConnection> {
  const nc = await connect({ servers: natsUrl });
  const jsm = await nc.jetstreamManager();
  await ensureStream(jsm);
  await ensureConsumer(jsm);

  const js = nc.jetstream();
  const consumer = await js.consumers.get(STREAM_NAME, CONSUMER_NAME);
  const messages = await consumer.consume();

  (async () => {
    for await (const msg of messages) {
      try {
        const event = JSON.parse(sc.decode(msg.data)) as LeadCreatedEvent;
        const tgUserId = event.tg_user_id;
        if (!tgUserId) {
          console.warn("[lead.created] missing tg_user_id", event);
          msg.ack();
          continue;
        }

        const text = formatLeadNotification(event);
        await bot.api.sendMessage(tgUserId, text, {
          reply_markup: leadKeyboard(event.lead_id),
        });
        incLeadsDelivered();
        msg.ack();
      } catch (err) {
        console.error("failed to handle lead.created", err);
        msg.nak();
      }
    }
  })();

  return nc;
}

export type { LeadCreatedEvent };
