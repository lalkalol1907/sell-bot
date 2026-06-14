let leadsDelivered = 0;
let workerAlerts = 0;
let botUpdates = 0;

export function incLeadsDelivered() {
  leadsDelivered += 1;
}

export function incWorkerAlerts() {
  workerAlerts += 1;
}

export function incBotUpdates() {
  botUpdates += 1;
}

export function healthResponse(): Response {
  return new Response(JSON.stringify({ status: "ok" }), {
    headers: { "Content-Type": "application/json" },
  });
}

export function metricsResponse(): Response {
  const body = [
    "# HELP seller_bot_leads_delivered_total Lead notifications sent to Telegram",
    "# TYPE seller_bot_leads_delivered_total counter",
    `seller_bot_leads_delivered_total ${leadsDelivered}`,
    "# HELP seller_bot_worker_alerts_total Worker status alerts sent",
    "# TYPE seller_bot_worker_alerts_total counter",
    `seller_bot_worker_alerts_total ${workerAlerts}`,
    "# HELP seller_bot_updates_total Telegram updates handled",
    "# TYPE seller_bot_updates_total counter",
    `seller_bot_updates_total ${botUpdates}`,
  ].join("\n");
  return new Response(`${body}\n`, {
    headers: { "Content-Type": "text/plain; version=0.0.4" },
  });
}

/** @deprecated use startHttpServer from transport.ts */
export function startMetricsServer(port: number) {
  Bun.serve({
    port,
    hostname: "0.0.0.0",
    fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === "/health") return healthResponse();
      if (url.pathname === "/metrics") return metricsResponse();
      return new Response("not found", { status: 404 });
    },
  });
  console.log(`metrics server on :${port}`);
}
