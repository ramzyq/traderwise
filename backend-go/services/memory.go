package services

import "sync"

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type MemoryStore struct {
	mu    sync.RWMutex
	store map[string][]Message
}

var Memory = &MemoryStore{
	store: make(map[string][]Message),
}

const maxHistory = 20

func (m *MemoryStore) Get(userID string) []Message {
	m.mu.RLock()
	defer m.mu.RUnlock()
	history := m.store[userID]
	result := make([]Message, len(history))
	copy(result, history)
	return result
}

func (m *MemoryStore) Save(userID string, history []Message) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if len(history) > maxHistory {
		history = history[len(history)-maxHistory:]
	}
	m.store[userID] = history
}

func (m *MemoryStore) Clear(userID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.store, userID)
}
