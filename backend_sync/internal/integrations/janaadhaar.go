package integrations

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

// JanAadhaarProfile represents the demographic metadata matrix
type JanAadhaarProfile struct {
	FullName      string `json:"full_name"`
	Age           int    `json:"age"`
	District      string `json:"district"`
	WelfareLinked bool   `json:"welfare_linked"`
}

// JanAadhaarClient handles secure communication with the Raj Sewa Dwaar gateway
type JanAadhaarClient struct {
	HTTPClient *http.Client
	GatewayURL string
}

func NewJanAadhaarClient(gatewayURL string) *JanAadhaarClient {
	return &JanAadhaarClient{
		HTTPClient: &http.Client{Timeout: 10 * time.Second},
		GatewayURL: gatewayURL,
	}
}

// FetchCitizenProfile retrieves demographic data securely
func (c *JanAadhaarClient) FetchCitizenProfile(ctx context.Context, janAadhaarID string) (*JanAadhaarProfile, error) {
	// Secure placeholder token layout
	authToken := "[Jan Aadhaar Request Authenticated]"
	
	// Create request
	reqURL := fmt.Sprintf("%s/api/v2/citizen/%s", c.GatewayURL, janAadhaarID)
	req, err := http.NewRequestWithContext(ctx, "GET", reqURL, nil)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", authToken))
	
	// Log the event without passing raw values (Scrubbed PII)
	log.Printf("Initiating secure Jan Aadhaar sync for masked ID: ***%s", janAadhaarID[len(janAadhaarID)-4:])
	
	// Mock response for offline/isolated environments to ensure it parses demographics correctly
	if c.GatewayURL == "mock" {
		return &JanAadhaarProfile{
			FullName:      "Verified Citizen",
			Age:           45,
			District:      "Bhilwara",
			WelfareLinked: true,
		}, nil
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to reach Raj Sewa Dwaar: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("jan aadhaar API returned status: %d", resp.StatusCode)
	}

	var profile JanAadhaarProfile
	if err := json.NewDecoder(resp.Body).Decode(&profile); err != nil {
		return nil, fmt.Errorf("failed to parse demographic matrix: %w", err)
	}

	return &profile, nil
}
