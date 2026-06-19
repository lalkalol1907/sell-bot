import { Hono } from "hono";
import { grpcErrorMessage } from "../grpc/clients.js";
import { requireSeller } from "../middleware.js";

export function createSellerRoutes() {
  const app = new Hono();

  app.use("/seller/*", requireSeller);

  app.get("/seller/stats", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const days = Number(c.req.query("days") ?? "30");
    const stats = await grpc.getLeadStats(sellerId, days);
    return c.json(stats);
  });

  app.get("/seller/products", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const products = await grpc.listProducts(sellerId);
    return c.json({ products });
  });

  app.post("/seller/products", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const body = await c.req.json<{ product: Record<string, unknown> }>();
    const p = body.product ?? {};

    try {
      const product = await grpc.createProduct({
        seller_id: sellerId,
        title: String(p.title ?? ""),
        price: String(p.price ?? ""),
        currency: String(p.currency ?? "RUB"),
        keywords: Array.isArray(p.keywords) ? p.keywords.map(String) : [],
      });
      return c.json(product, 201);
    } catch (err) {
      return c.json({ error: grpcErrorMessage(err) || "invalid product" }, 400);
    }
  });

  app.patch("/seller/products/:id", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const id = Number(c.req.param("id"));
    const body = await c.req.json<{ product: Record<string, unknown> }>();
    const p = body.product ?? {};

    try {
      const product = await grpc.updateProduct({
        id,
        seller_id: sellerId,
        title: String(p.title ?? ""),
        price: String(p.price ?? ""),
        currency: String(p.currency ?? "RUB"),
        keywords: Array.isArray(p.keywords) ? p.keywords.map(String) : [],
        is_active: p.is_active !== undefined ? Boolean(p.is_active) : true,
      });
      return c.json(product);
    } catch (err) {
      return c.json({ error: grpcErrorMessage(err) || "invalid product" }, 400);
    }
  });

  app.delete("/seller/products/:id", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const id = Number(c.req.param("id"));
    const success = await grpc.deleteProduct(id, sellerId);
    return c.json({ success });
  });

  app.get("/seller/leads", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const status = c.req.query("status") ?? "";
    const limit = Number(c.req.query("limit") ?? "50");
    const offset = Number(c.req.query("offset") ?? "0");
    const result = await grpc.listLeads(sellerId, status, limit, offset);
    return c.json(result);
  });

  app.patch("/seller/leads/:id", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const id = Number(c.req.param("id"));
    const body = await c.req.json<{ lead: { status?: string } }>();
    const status = body.lead?.status ?? "";

    try {
      const lead = await grpc.updateLeadStatus(id, sellerId, status);
      return c.json(lead);
    } catch (err) {
      return c.json({ error: grpcErrorMessage(err) || "invalid lead" }, 400);
    }
  });

  app.get("/seller/workers", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const workers = await grpc.listWorkers(sellerId);
    return c.json({ workers });
  });

  app.patch("/seller/workers/:id/status", async (c) => {
    const grpc = c.get("grpc");
    const id = Number(c.req.param("id"));
    const body = await c.req.json<{ worker: { status?: string } }>();
    const status = body.worker?.status ?? "";

    try {
      const worker = await grpc.updateWorkerStatus(id, status);
      return c.json(worker);
    } catch (err) {
      return c.json({ error: grpcErrorMessage(err) || "invalid worker" }, 400);
    }
  });

  app.patch("/seller/settings", async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");
    const body = await c.req.json<{ settings: { sensitivity?: string } }>();
    const sensitivity = body.settings?.sensitivity ?? "";

    try {
      const seller = await grpc.updateSeller(sellerId, sensitivity);
      return c.json({ id: seller.id, sensitivity: seller.sensitivity });
    } catch (err) {
      return c.json({ error: grpcErrorMessage(err) || "invalid settings" }, 400);
    }
  });

  return app;
}
