let leadsDelivered = 0;
let workerAlerts = 0;

export function incLeadsDelivered() {
  leadsDelivered += 1;
}

export function incWorkerAlerts() {
  workerAlerts += 1;
}

export function startMetricsServer(port: number) {
  Bun.serve({
    port,
    fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === "/health") {
        return new Response(JSON.stringify({ status: "ok" }), {
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.pathname === "/metrics") {
        const body = [
          "# HELP seller_bot_leads_delivered_total Lead notifications sent to Telegram",
          "# TYPE seller_bot_leads_delivered_total counter",
          `seller_bot_leads_delivered_total ${leadsDelivered}`,
          "# HELP seller_bot_worker_alerts_total Worker status alerts sent",
          "# TYPE seller_bot_worker_alerts_total counter",
          `seller_bot_worker_alerts_total ${workerAlerts}`,
        ].join("\n");
        return new Response(`${body}\n`, {
          headers: { "Content-Type": "text/plain; version=0.0.4" },
        });
      }
      return new Response("not found", { status: 404 });
    },
  });
  console.log(`metrics server on :${port}`);
}
