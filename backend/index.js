import "dotenv/config";
import express from "express";
import { handleWebhook, verifyWebhook } from "./webhook.js";

const app = express();
app.use(express.json());

// ── Webhook verification (Meta requires this on setup) ──────────────────────
app.get("/webhook", verifyWebhook);

// ── Incoming messages ───────────────────────────────────────────────────────
app.post("/webhook", handleWebhook);

// ── Health check ────────────────────────────────────────────────────────────
app.get("/", (_req, res) => res.send("TraderWise Bot is running ✅"));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 TraderWise listening on port ${PORT}`));