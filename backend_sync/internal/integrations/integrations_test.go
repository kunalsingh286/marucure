package integrations

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	
	"rajcxr/sync_backend/internal/db"
)

func TestJanAadhaarSync(t *testing.T) {
	client := NewJanAadhaarClient("mock")
	profile, err := client.FetchCitizenProfile(context.Background(), "9999999999")
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	
	if profile.FullName != "Verified Citizen" || profile.District != "Bhilwara" {
		t.Errorf("Unexpected demographic matrix: %+v", profile)
	}
}

func TestSSOMiddleware(t *testing.T) {
	handler := SSOMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		claims, ok := r.Context().Value(SSOContextKey).(*SSOTokenClaims)
		if !ok || claims == nil {
			t.Fatal("Claims not found in context")
		}
		
		if claims.OfficialID != "RJ-MED-491" {
			t.Errorf("Unexpected official ID in claims: %s", claims.OfficialID)
		}
		
		w.WriteHeader(http.StatusOK)
	}))

	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer valid_mock_sso_token")
	
	rr := httptest.NewRecorder()
	handler.ServeHTTP(rr, req)
	
	if rr.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %d", rr.Code)
	}
	
	// Test invalid token
	reqInvalid, _ := http.NewRequest("GET", "/", nil)
	reqInvalid.Header.Set("Authorization", "Bearer invalid_token")
	
	rrInvalid := httptest.NewRecorder()
	handler.ServeHTTP(rrInvalid, reqInvalid)
	
	if rrInvalid.Code != http.StatusUnauthorized {
		t.Errorf("Expected 401 Unauthorized for invalid token, got %d", rrInvalid.Code)
	}
}

func TestReferralRouterSegmentsRisk(t *testing.T) {
	router := NewReferralRouter()
	
	// Test High Risk Profile
	highRiskRecord := db.ScreeningRecord{
		ScreeningID: "SC-HIGH-001",
		FullName: "High Risk Miner",
		RiskScore: 8.5,
	}
	
	err := router.EvaluateAndRoute(context.Background(), highRiskRecord, "Jodhpur")
	if err != nil {
		t.Fatalf("Failed to route high risk record: %v", err)
	}
	
	// Test Low Risk Profile
	lowRiskRecord := db.ScreeningRecord{
		ScreeningID: "SC-LOW-002",
		FullName: "Low Risk Miner",
		RiskScore: 4.0,
	}
	
	err = router.EvaluateAndRoute(context.Background(), lowRiskRecord, "Jodhpur")
	if err != nil {
		t.Fatalf("Expected no error for low risk record, got %v", err)
	}
}

func TestSMSGatewayWebhook(t *testing.T) {
	client := NewSMSGatewayClient("mock")
	err := client.SendStatusUpdate(context.Background(), "919999999999", "Test Miner", "TRK-001-CXR", "2026-08-15")
	if err != nil {
		t.Fatalf("Expected no error from SMS gateway, got %v", err)
	}
}
