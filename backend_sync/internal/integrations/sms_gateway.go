package integrations

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

type SMSGatewayClient struct {
	EndpointURL string
	HTTPClient  *http.Client
}

func NewSMSGatewayClient(endpointURL string) *SMSGatewayClient {
	return &SMSGatewayClient{
		EndpointURL: endpointURL,
		HTTPClient:  &http.Client{},
	}
}

// OfficialStatePayload maps to the official payload configurations used by government utilities
type OfficialStatePayload struct {
	MobileNumber   string `json:"mobile_number"`
	MessageBody    string `json:"message_body"`
	TemplateID     string `json:"template_id"`
	ReferenceToken string `json:"reference_token"`
}

func (s *SMSGatewayClient) SendStatusUpdate(ctx context.Context, mobileNumber, patientName, referenceToken string, boardDate string) error {
	// Message template securely binds the tracking reference token
	messageBody := fmt.Sprintf("MaruCure Silicosis Triage Engine Alert: %s, your Silicosis clinical evaluation is scheduled for %s. Tracking Token: %s", 
		patientName, boardDate, referenceToken)
		
	payload := OfficialStatePayload{
		MobileNumber:   mobileNumber,
		MessageBody:    messageBody,
		TemplateID:     "RAJ-HEALTH-CXR-001",
		ReferenceToken: referenceToken,
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to serialize SMS payload: %w", err)
	}
	
	if s.EndpointURL == "mock" {
		log.Printf("Mock SMS Dispatched to ***%s: %s", mobileNumber[len(mobileNumber)-4:], messageBody)
		return nil
	}
	
	req, err := http.NewRequestWithContext(ctx, "POST", s.EndpointURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := s.HTTPClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send SMS via state gateway: %w", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		return fmt.Errorf("SMS gateway returned non-success code: %d", resp.StatusCode)
	}
	
	return nil
}
