package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

func SendMessage(to, text string) error {
	phoneNumberID := os.Getenv("WHATSAPP_PHONE_NUMBER_ID")
	accessToken := os.Getenv("WHATSAPP_ACCESS_TOKEN")

	url := fmt.Sprintf("https://graph.facebook.com/v19.0/%s/messages", phoneNumberID)

	payload := map[string]any{
		"messaging_product": "whatsapp",
		"to":                to,
		"type":              "text",
		"text":              map[string]string{"body": text},
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", url, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+accessToken)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("WhatsApp API error (%d): %s", resp.StatusCode, string(b))
	}
	return nil
}

func ResolveAudioURL(mediaID string) (string, error) {
	accessToken := os.Getenv("WHATSAPP_ACCESS_TOKEN")
	url := fmt.Sprintf("https://graph.facebook.com/v19.0/%s", mediaID)

	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+accessToken)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var result map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	audioURL, _ := result["url"].(string)
	return audioURL, nil
}
