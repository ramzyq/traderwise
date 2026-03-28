/**
 * In-memory conversation history for TraderWise.
 * Resets when the server restarts.
 * Swap for Redis in production.
 */

const store = new Map();
const MAX_HISTORY = 20; // Keep last 20 messages per trader

export async function getHistory(userId) {
  return store.get(userId) ?? [];
}

export async function saveHistory(userId, history) {
  store.set(userId, history.slice(-MAX_HISTORY));
}

export async function clearHistory(userId) {
  store.delete(userId);
}