const { transcribeAudio, chat } = require("../services/aiClient");

function toTwiml(message) {
  return `<?xml version="1.0" encoding="UTF-8"?><Response><Message>${escapeXml(message)}</Message></Response>`;
}

function escapeXml(input) {
  return String(input)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function normalizePhone(phone) {
  if (!phone) return "unknown";
  return String(phone).trim();
}

function extractIncomingMessage(body) {
  const text = typeof body.Body === "string" ? body.Body.trim() : "";
  if (text.length > 0) {
    return { kind: "text", message: text };
  }

  const numMedia = Number(body.NumMedia || 0);
  if (numMedia > 0 && body.MediaUrl0) {
    return { kind: "audio", audioUrl: body.MediaUrl0 };
  }

  return { kind: "empty" };
}

function createWebhookHandler({ aiServiceUrl }) {
  return async (req, res) => {
    const from = normalizePhone(req.body.From);
    const incoming = extractIncomingMessage(req.body);

    try {
      let messageForChat = "";

      if (incoming.kind === "text") {
        messageForChat = incoming.message;
      } else if (incoming.kind === "audio") {
        const transcribeResult = await transcribeAudio({
          aiServiceUrl,
          audioUrl: incoming.audioUrl,
          phone: from
        });
        messageForChat = transcribeResult.text || "";
      } else {
        res
          .status(200)
          .type("text/xml")
          .send(toTwiml("Please send a text or voice note."));
        return;
      }

      if (!messageForChat) {
        res
          .status(200)
          .type("text/xml")
          .send(toTwiml("I could not understand that voice note. Please try again."));
        return;
      }

      const chatResult = await chat({
        aiServiceUrl,
        message: messageForChat,
        phone: from
      });

      const reply = chatResult.reply || "Mepa wo kyew, san ka bio.";

      res.status(200).type("text/xml").send(toTwiml(reply));
    } catch (error) {
      console.error("Webhook error:", error.message);
      res
        .status(200)
        .type("text/xml")
        .send(toTwiml("There was a temporary issue. Please try again shortly."));
    }
  };
}

module.exports = {
  createWebhookHandler
};
