package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"traderwise/backend/services"
)

// ── Meta webhook structs ──────────────────────────────────────────────────

type webhookBody struct {
	Object string  `json:"object"`
	Entry  []entry `json:"entry"`
}

type entry struct {
	Changes []change `json:"changes"`
}

type change struct {
	Value changeValue `json:"value"`
}

type changeValue struct {
	Messages []incomingMessage `json:"messages"`
}

type incomingMessage struct {
	From  string       `json:"from"`
	Type  string       `json:"type"`
	Text  *textContent `json:"text"`
	Audio *mediaRef    `json:"audio"`
}

type textContent struct {
	Body string `json:"body"`
}

type mediaRef struct {
	ID string `json:"id"`
}

// ── Verify ────────────────────────────────────────────────────────────────

func VerifyWebhook(w http.ResponseWriter, r *http.Request) {
	mode      := r.URL.Query().Get("hub.mode")
	token     := r.URL.Query().Get("hub.verify_token")
	challenge := r.URL.Query().Get("hub.challenge")

	if mode == "subscribe" && token == os.Getenv("WHATSAPP_VERIFY_TOKEN") {
		log.Println("Webhook verified")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(challenge))
		return
	}

	log.Println("Webhook verification failed")
	http.Error(w, "Forbidden", http.StatusForbidden)
}

// ── Handle incoming messages ──────────────────────────────────────────────

func HandleWebhook(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK) // Respond immediately to Meta

	var body webhookBody
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		log.Println("Failed to decode webhook body:", err)
		return
	}

	if body.Object != "whatsapp_business_account" {
		return
	}

	if len(body.Entry) == 0 || len(body.Entry[0].Changes) == 0 {
		return
	}

	messages := body.Entry[0].Changes[0].Value.Messages
	if len(messages) == 0 {
		return
	}

	msg  := messages[0]
	from := msg.From
	log.Printf("Message from [%s] type: %s", from, msg.Type)

	// ── Built-in commands ────────────────────────────────────────────────
	if msg.Type == "text" && msg.Text != nil {
		text := strings.ToLower(strings.TrimSpace(msg.Text.Body))

		if text == "start" {
			services.Memory.Clear(from)
			services.SendMessage(from,
				"Hello! I'm Ama, your TraderWise business partner.\n\n"+
					"I'm here to help you think through your trading — restocking, pricing, credit, savings, and more.\n\n"+
					"I know you're busy, so I'll keep things short and practical.\n\n"+
					"What's going on with your business today?",
			)
			return
		}

		if text == "reset" || text == "start over" {
			services.Memory.Clear(from)
			services.SendMessage(from, "Chat cleared. What's on your mind with the business?")
			return
		}

		if text == "help" {
			services.SendMessage(from,
				"TraderWise commands:\n\n"+
					"start — introduce yourself and begin\n"+
					"reset — clear chat history\n"+
					"help — show this menu\n\n"+
					"Or just tell me what's going on with your business.",
			)
			return
		}
	}

	// ── Route message to AI service ──────────────────────────────────────
	var messageText string

	switch msg.Type {
	case "text":
		if msg.Text != nil {
			messageText = strings.TrimSpace(msg.Text.Body)
		}

	case "audio":
		if msg.Audio == nil {
			services.SendMessage(from, "Could not process the voice note. Please try again.")
			return
		}
		audioURL, err := services.ResolveAudioURL(msg.Audio.ID)
		if err != nil || audioURL == "" {
			log.Println("Failed to resolve audio URL:", err)
			services.SendMessage(from, "Could not process the voice note. Please try again.")
			return
		}
		text, err := services.Transcribe(audioURL, from)
		if err != nil {
			log.Println("Transcription error:", err)
			services.SendMessage(from, "Could not transcribe the voice note. Please try again.")
			return
		}
		messageText = text

	default:
		services.SendMessage(from, "Sorry, I can only read text and voice messages. Please type your question.")
		return
	}

	if messageText == "" {
		services.SendMessage(from, "I could not understand that. Please try again.")
		return
	}

	reply, err := services.Chat(messageText, from)
	if err != nil {
		log.Println("Chat error:", err)
		services.SendMessage(from, "Something went wrong. Please try again in a moment.")
		return
	}
	if reply == "" {
		reply = "Mepa wo kyew, san ka bio."
	}

	history := services.Memory.Get(from)
	history = append(history, services.Message{Role: "user", Content: messageText})
	history = append(history, services.Message{Role: "assistant", Content: reply})
	services.Memory.Save(from, history)

	if err := services.SendMessage(from, reply); err != nil {
		log.Println("Failed to send message:", err)
	} else {
		log.Printf("Replied to [%s]", from)
	}
}
