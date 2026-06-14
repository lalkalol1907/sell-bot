import { InlineKeyboard } from "grammy";
import type { Bot } from "grammy";
import { connect, StringCodec } from "nats";
import type { BotContext } from "../types.js";
import { formatLeadNotification, type LeadCreatedEvent } from "../utils/lead-notification.js";

const sc = StringCodec();

export type { LeadCreatedEvent };

function leadKeyboard(leadId: number) {
  return new InlineKeyboard()
    .text("В работе", `lead:contacted:${leadId}`)
    .text("Закрыть", `lead:closed:${leadId}`)
    .row()
    .text("Спам", `lead:spam:${leadId}`);
}

export async function subscribeLeadCreated(bot: Bot<BotContext>, natsUrl: string) {
  const nc = await connect({ servers: natsUrl });
  const sub = nc.subscribe("lead.created");

  (async () => {
    for await (const msg of sub) {
      try {
        const event = JSON.parse(sc.decode(msg.data)) as LeadCreatedEvent;
        const tgUserId = event.tg_user_id;
        if (!tgUserId) {
          console.warn("[lead.created] missing tg_user_id", event);
          continue;
        }

        const text = formatLeadNotification(event);

        await bot.api.sendMessage(tgUserId, text, {
          reply_markup: leadKeyboard(event.lead_id),
        });
      } catch (err) {
        console.error("failed to handle lead.created", err);
      }
    }
  })();

  return nc;
}
