import express from "express";
import { verifyWebhook, handleWebhook } from "./webhooks/whatsapp.js";

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => res.json({ ok: true, service: "backend" }));

// Meta webhook verification (GET) + incoming messages (POST)
app.get("/webhook",  verifyWebhook);
app.post("/webhook", handleWebhook);

export default app;
