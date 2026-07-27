package api

import (
	"encoding/json"
	"math/rand"
	"net/http"
	"time"
)

// ChaosThrottler simulates poor cellular connectivity by injecting latency or random 503 drops.
func ChaosThrottler(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 15% chance to simulate a complete cellular dropout
		if rand.Float32() < 0.15 {
			http.Error(w, `{"error": "Simulated 503 Service Unavailable (Network Drop)"}`, http.StatusServiceUnavailable)
			return
		}
		
		// Simulate 1 to 3 seconds of high-latency rural network delay
		delay := time.Duration(rand.Intn(2000)+1000) * time.Millisecond
		time.Sleep(delay)
		
		next(w, r)
	}
}

func HandleMockJanAadhaar(w http.ResponseWriter, r *http.Request) {
	var payload struct {
		ID string `json:"jan_aadhaar_number"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid Request", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if payload.ID == "1234567890" {
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status": "success",
			"profile": map[string]string{
				"name": "Ramesh Kumar",
				"age": "45",
				"occupation": "Sandstone Driller",
				"district": "Jodhpur",
			},
		})
		return
	}

	http.Error(w, `{"error": "Profile not found or invalid ID"}`, http.StatusNotFound)
}

func HandleMockRajSSO(w http.ResponseWriter, r *http.Request) {
	// Returns a realistic mock JWT containing specific state roles
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "success",
		"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_payload.mock_signature",
		"roles": []string{"CAMP_COORDINATOR", "BMO_JODHPUR"},
	})
}
