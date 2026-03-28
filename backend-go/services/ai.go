package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

func aiServiceURL() string {
	url := os.Getenv("AI_SERVICE_URL")
	if url == "" {
		url = "http://localhost:8000"
	}
	return strings.TrimRight(url, "/")
}

func postJSON(endpoint string, payload any) (map[string]any, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(aiServiceURL()+endpoint, "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("AI service error (%d): %s", resp.StatusCode, string(b))
	}

	var result map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}

func Chat(message, phone string) (string, error) {
	result, err := postJSON("/chat", map[string]string{
		"message": message,
		"phone":   phone,
	})
	if err != nil {
		return "", err
	}
	reply, _ := result["reply"].(string)
	return reply, nil
}

func Transcribe(audioURL, phone string) (string, error) {
	result, err := postJSON("/transcribe", map[string]string{
		"audio_url":    audioURL,
		"phone":        phone,
		"access_token": os.Getenv("WHATSAPP_ACCESS_TOKEN"),
	})
	if err != nil {
		return "", err
	}
	text, _ := result["text"].(string)
	return text, nil
}
