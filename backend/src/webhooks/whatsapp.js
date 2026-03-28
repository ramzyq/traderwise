import { sendWhatsAppMessage } from "../services/whatsapp.js";
import { chat, transcribeAudio } from "../services/aiClient.js";
import { getHistory, saveHistory, clearHistory } from "../services/memory.js";

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";

// ── Meta webhook verification ─────────────────────────────────────────────
export function verifyWebhook(req, res) {
  const mode      = req.query["hub.mode"];
  const token     = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === process.env.WHATSAPP_VERIFY_TOKEN) {
    console.log("Webhook verified");
    return res.status(200).send(challenge);
  }
  console.error("Webhook verification failed");
  res.sendStatus(403);
}

// ── Handle incoming messages ──────────────────────────────────────────────
export async function handleWebhook(req, res) {
  res.sendStatus(200); // Respond immediately to Meta

  const body = req.body;
  if (body.object !== "whatsapp_business_account") return;

  const message = body.entry?.[0]?.changes?.[0]?.value?.messages?.[0];
  if (!message) return;

  const from = message.from;
  console.log(`Message from [${from}] type: ${message.type}`);

  // ── Built-in commands ────────────────────────────────────────────────────
  if (message.type === "text") {
    const text = message.text.body.trim().toLowerCase();

    if (text === "reset" || text === "start over") {
      await clearHistory(from);
      await sendWhatsAppMessage(from, "Chat cleared! Let's start fresh. How can TraderWise help your business today?");
      return;
    }

    if (text === "help") {
      await sendWhatsAppMessage(from,
        "TraderWise Commands:\n\n" +
        "• Just type your question or business problem\n" +
        "• reset — clear chat history\n" +
        "• help — show this menu\n\n" +
        "I can help with pricing, profits, savings, and stock advice."
      );
      return;
    }
  }

  try {
    let messageText = "";

    if (message.type === "text") {
      messageText = message.text.body.trim();
    } else if (message.type === "audio") {
      const audioUrl = message.audio?.id
        ? await resolveAudioUrl(message.audio.id)
        : null;

      if (!audioUrl) {
        await sendWhatsAppMessage(from, "Could not process the voice note. Please try again.");
        return;
      }

      const result = await transcribeAudio({ aiServiceUrl: AI_SERVICE_URL, audioUrl, phone: from });
      messageText = result.text || "";
    } else {
      await sendWhatsAppMessage(from, "Sorry, I can only read text and voice messages. Please type your question.");
      return;
    }

    if (!messageText) {
      await sendWhatsAppMessage(from, "I could not understand that. Please try again.");
      return;
    }

    const result = await chat({ aiServiceUrl: AI_SERVICE_URL, message: messageText, phone: from });
    const reply  = result.reply || "Mepa wo kyew, san ka bio.";

    const history = await getHistory(from);
    history.push({ role: "user",      content: messageText });
    history.push({ role: "assistant", content: reply });
    await saveHistory(from, history);

    await sendWhatsAppMessage(from, reply);
    console.log(`Replied to [${from}]`);
  } catch (err) {
    console.error("Webhook error:", err.message);
    await sendWhatsAppMessage(from, "Something went wrong. Please try again in a moment.");
  }
}

// ── Resolve WhatsApp audio media ID to a download URL ────────────────────
async function resolveAudioUrl(mediaId) {
  const response = await fetch(`https://graph.facebook.com/v19.0/${mediaId}`, {
    headers: { Authorization: `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}` },
  });
  if (!response.ok) return null;
  const data = await response.json();
  return data.url || null;
}
