function buildUrl(base, path) {
  return `${base.replace(/\/$/, "")}${path}`;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`AI service request failed (${response.status}): ${body}`);
  }

  return response.json();
}

export async function transcribeAudio({ aiServiceUrl, audioUrl, phone }) {
  const url = buildUrl(aiServiceUrl, "/transcribe");
  return postJson(url, { audio_url: audioUrl, phone });
}

export async function chat({ aiServiceUrl, message, phone }) {
  const url = buildUrl(aiServiceUrl, "/chat");
  return postJson(url, { message, phone });
}
