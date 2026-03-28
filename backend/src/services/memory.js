/**
 * In-memory conversation history.
 * Resets on server restart — Python AI service handles persistent DB storage.
 */

const store = new Map();
const MAX_HISTORY = 20;

export async function getHistory(userId) {
  return store.get(userId) ?? [];
}

export async function saveHistory(userId, history) {
  store.set(userId, history.slice(-MAX_HISTORY));
}

export async function clearHistory(userId) {
  store.delete(userId);
}
