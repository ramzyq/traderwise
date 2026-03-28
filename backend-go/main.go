package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"traderwise/backend/handlers"

	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000"
	}

	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"ok": true, "service": "backend"})
	})

	mux.HandleFunc("GET /webhook",  handlers.VerifyWebhook)
	mux.HandleFunc("POST /webhook", handlers.HandleWebhook)

	log.Printf("Backend running on port %s", port)
	log.Printf("AI service target: %s", aiServiceURL)

	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}
