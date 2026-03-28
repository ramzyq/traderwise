const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

const SYSTEM_PROMPT = `You are TraderWise, an AI business co-pilot for informal market traders in Ghana. Keep replies short, practical, use Ghana Cedis. Respond in the user's language (English, Twi, or Dagbani).`;

export async function getAIReply(userMessage, conversationHistory = []) {
  const contents = [
    { role: "user", parts: [{ text: SYSTEM_PROMPT }] },
    { role: "model", parts: [{ text: "Understood! I am TraderWise." }] },
    ...conversationHistory.map(msg => ({
      role: msg.role === "assistant" ? "model" : "user",
      parts: [{ text: msg.content }]
    })),
    { role: "user", parts: [{ text: userMessage }] }
  ];

  const response = await fetch(`${GEMINI_API_URL}?key=AIzaSyBMrWPijsXefXKCayls461prhHfIiPPQRk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contents }),
  });

  const data = await response.json();
  console.log("Gemini response:", JSON.stringify(data));
if (!data.candidates || !data.candidates[0]) {
  throw new Error("No response from Gemini: " + JSON.stringify(data));
}
return data.candidates[0].content.parts[0].text;
}