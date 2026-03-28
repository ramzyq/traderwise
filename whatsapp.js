const WHATSAPP_API_URL = `https://graph.facebook.com/v19.0/1050575971469681/messages`;

export async function sendWhatsAppMessage(to, text) {
  const payload = {
    messaging_product: "whatsapp",
    to,
    type: "text",
    text: { body: text },
  };

  const response = await fetch(WHATSAPP_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer EAAU6rMEJ704BRLFS4zVpTEd48qTx4hubAZBaKNIXkpDJ0DDoHZCRZBQrWlA3ldiDCzXO2C59GrwNgDoXgSr9JaOvLbZAPfd4kwQ4C7ZCS7WKsOJji1UT6tdDYJ0gCGfu8X4PicnIN6UjG4vh7LJcPwG6OBeqs8Q8duidZADLufuZCJibHNwRysazHxeT3Ts0W8ZAxZBPX4L4X7qWbxFEOJTr9DRn3ZAR0cbTR1brioGpuZCSN7C81JUpsrgPxfV5ZAHqiXHe7E9Rq1mS7qpDVHNVz9VFZBi4d`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`WhatsApp API error: ${JSON.stringify(error)}`);
  }

  return response.json();
}