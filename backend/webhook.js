import { sendWhatsAppMessage } from "./whatsapp.js";
import { getAIReply } from "./ai.js";
import { getHistory, saveHistory, clearHistory } from "./memory.js";

// ── Meta webhook verification ───────────────────────────────────────────────
export function verifyWebhook(req, res) {
  const VERIFY_TOKEN = process.env.WHATSAPP_VERIFY_TOKEN;
  const mode      = req.query["hub.mode"];
  const token     = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("✅ Webhook verified");
    return res.status(200).send(challenge);
  }
  console.error("❌ Webhook verification failed");
  res.sendStatus(403);
}

// ── Handle incoming messages ─────────────────────────────────────────────────
export async function handleWebhook(req, res) {
  res.sendStatus(200); // Always respond immediately

  const body = req.body;
  if (body.object !== "whatsapp_business_account") return;

  const entry   = body.entry?.[0];
  const changes = entry?.changes?.[0];
  const value   = changes?.value;
  if (!value?.messages) return;

  const message = value.messages[0];
  const from    = message.from;

  console.log(`📩 Message from [${from}] type: ${message.type}`);

  // ── Built-in commands ──────────────────────────────────────────────────────
  if (message.type === "text") {
    const text = message.text.body.trim().toLowerCase();

    if (text === "reset" || text === "start over") {
      await clearHistory(from);
      await sendWhatsAppMessage(from,
        "Chat cleared! 🔄 Let's start fresh. How can TraderWise help your business today?");
      return;
    }

    if (text === "help") {
      await sendWhatsAppMessage(from,
        "TraderWise Commands:\n\n" +
        "• Just type your question or business problem\n" +
        "• *reset* — clear chat history\n" +
        "• *help* — show this menu\n\n" +
        "I can help with pricing, profits, savings, stock advice and more 📊");
      return;
    }
  }

  // ── Handle unsupported message types ──────────────────────────────────────
  if (message.type !== "text") {
    await sendWhatsAppMessage(from,
      "Sorry, I can only read text messages for now. Please type your question 🙏");
    return;
  }

  const userText = message.text.body.trim();

  try {
    const history  = await getHistory(from);
    const aiReply  = await getAIReply(userText, history);

    history.push({ role: "user",      content: userText });
    history.push({ role: "assistant", content: aiReply  });
    await saveHistory(from, history);

    await sendWhatsAppMessage(from, aiReply);
    console.log(`✅ Replied to [${from}]`);
  } catch (err) {
    console.error("Error:", err.message);
    await sendWhatsAppMessage(from,
      "Something went wrong on my end. Please try again in a moment 🙁");
  }
}