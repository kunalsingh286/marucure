package integrations

import (
	"context"
	"fmt"
	"log"
	
	"rajcxr/sync_backend/internal/db"
)

type ReferralPayload struct {
	ScreeningID   string
	PatientName   string
	RiskScore     float64
	TargetBoard   string // Target District Pneumoconiosis Board
}

type ReferralRouter struct {
	// In a real system, this would hold MQ/Kafka connections
}

func NewReferralRouter() *ReferralRouter {
	return &ReferralRouter{}
}

// EvaluateAndRoute intercepts database worker records and pushes high-risk profiles
func (r *ReferralRouter) EvaluateAndRoute(ctx context.Context, record db.ScreeningRecord, district string) error {
	// Programmatic event router engine based on Risk Index
	if record.RiskScore >= 7.5 {
		payload := ReferralPayload{
			ScreeningID: record.ScreeningID,
			PatientName: record.FullName,
			RiskScore:   record.RiskScore,
			TargetBoard: fmt.Sprintf("%s District Pneumoconiosis Board", district),
		}
		
		// Automatically bypass secondary regional data queues
		err := r.pushToBoardQueue(ctx, payload)
		if err != nil {
			return fmt.Errorf("failed to route clinical case payload: %w", err)
		}
	}
	
	return nil
}

func (r *ReferralRouter) pushToBoardQueue(ctx context.Context, payload ReferralPayload) error {
	// Mocks the network call to the district board's queue
	log.Printf("URGENT REFERRAL DISPATCHED: Screening %s assigned directly to %s (Risk: %.1f)", 
		payload.ScreeningID, payload.TargetBoard, payload.RiskScore)
	return nil
}
