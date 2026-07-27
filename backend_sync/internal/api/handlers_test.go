package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"rajcxr/sync_backend/internal/cloud"
	"rajcxr/sync_backend/internal/db"
)

func TestHandleBatchSync(t *testing.T) {
	// Setup isolated integration suite
	// We pass a nil DB which internally short-circuits the Upsert routing (mocking pgxpool).
	database := &db.DB{Pool: nil}
	s3Client := cloud.NewS3Client("test-bucket")
	
	apiInstance := NewAPI(database, s3Client)
	router := apiInstance.Routes()

	validPayload := SyncPayload{
		ScreeningID:   "test-uuid-123",
		FullName:      "Test Miner",
		JanAadhaar:    "1234567890",
		RiskScore:     8.0,
		ClinicalFlag:  "FIR",
		SpirometryLog: "{}",
		HeatmapBase64: "c29tZV9kYXRh", // Base64 for "some_data"
		Signature:     "valid_mock_signature_123",
	}

	payloads := []SyncPayload{validPayload}
	body, _ := json.Marshal(payloads)

	req, _ := http.NewRequest("POST", "/sync", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	rr := httptest.NewRecorder()
	
	// Execute high-concurrency request handler
	router.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("Handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	expected := `{"status": "success"}`
	if rr.Body.String() != expected {
		t.Errorf("Handler returned unexpected body: got %v want %v", rr.Body.String(), expected)
	}
}

func BenchmarkHandleBatchSync(b *testing.B) {
	database := &db.DB{Pool: nil}
	s3Client := cloud.NewS3Client("test-bucket")
	
	apiInstance := NewAPI(database, s3Client)
	router := apiInstance.Routes()

	// Prepare payload array simulating parallel device uploads
	payloads := make([]SyncPayload, 100)
	for i := 0; i < 100; i++ {
		payloads[i] = SyncPayload{
			ScreeningID:   "test-uuid",
			FullName:      "Test Miner",
			JanAadhaar:    "1234567890",
			RiskScore:     5.0,
			ClinicalFlag:  "NORMAL",
			SpirometryLog: "{}",
			HeatmapBase64: "c29tZV9kYXRh", 
			Signature:     "valid_mock_signature_123",
		}
	}
	body, _ := json.Marshal(payloads)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req, _ := http.NewRequest("POST", "/sync", bytes.NewBuffer(body))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()
		router.ServeHTTP(rr, req)
	}
}
