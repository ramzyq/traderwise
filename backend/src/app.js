const express = require("express");
const { createWebhookHandler } = require("./webhooks/whatsapp");

function createApp({ aiServiceUrl }) {
  const app = express();

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  app.get("/health", (_req, res) => {
    res.json({ ok: true, service: "backend" });
  });

  app.post("/webhook", createWebhookHandler({ aiServiceUrl }));

  return app;
}

module.exports = { createApp };
