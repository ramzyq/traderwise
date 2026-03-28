import fs from "node:fs";
import path from "node:path";
import dotenv from "dotenv";
import express from "express";
import { handleWebhook, verifyWebhook } from "./webhook.js";

// Load env from DOTENV_PATH, then traderwise.env, then .env.
const envCandidates = [process.env.DOTENV_PATH, "traderwise.env", ".env"].filter(Boolean);
for (const candidate of envCandidates) {
	const fullPath = path.resolve(process.cwd(), candidate);
	if (fs.existsSync(fullPath)) {
		dotenv.config({ path: fullPath });
		break;
	}
}

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