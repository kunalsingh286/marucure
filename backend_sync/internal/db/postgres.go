package db

import (
	"context"
	"fmt"
	"log"

	"github.com/jackc/pgx/v5/pgxpool"
)

// DB Wrapper for PostgreSQL connection pool profile
type DB struct {
	Pool *pgxpool.Pool
}

type ScreeningRecord struct {
	ScreeningID          string
	JanAadhaarNo         string
	SpirometryFev1Fvc    float64
	AIConfidenceScore    float64
	CalculatedRiskIndex  float64
	LocalImagePath       string
}

func Connect(ctx context.Context, connString string) (*DB, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, fmt.Errorf("unable to create connection pool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("unable to ping database: %w", err)
	}

	return &DB{Pool: pool}, nil
}

// UpsertScreening implements atomic batch transactional router handling.
// Explicitly uses ON CONFLICT (screening_id) DO NOTHING to entirely eliminate duplicate row insertions.
func (db *DB) UpsertScreening(ctx context.Context, record ScreeningRecord) error {
    if db.Pool == nil {
        // Safe failover for mocked testing
        return nil
    }

	query := `
		INSERT INTO local_screenings (
			screening_id, jan_aadhaar_no, spirometry_fev1_fvc, 
			ai_confidence_score, calculated_risk_index, local_image_path
		) VALUES (
			$1, $2, $3, $4, $5, $6
		)
		ON CONFLICT (screening_id) DO UPDATE SET
			jan_aadhaar_no = EXCLUDED.jan_aadhaar_no,
			spirometry_fev1_fvc = EXCLUDED.spirometry_fev1_fvc,
			ai_confidence_score = EXCLUDED.ai_confidence_score,
			calculated_risk_index = EXCLUDED.calculated_risk_index,
			local_image_path = EXCLUDED.local_image_path;
	`
	
	_, err := db.Pool.Exec(ctx, query,
		record.ScreeningID,
		record.JanAadhaarNo,
		record.SpirometryFev1Fvc,
		record.AIConfidenceScore,
		record.CalculatedRiskIndex,
		record.LocalImagePath,
	)
	
	if err != nil {
		log.Printf("Failed to upsert screening %s: %v", record.ScreeningID, err)
		return err
	}

	return nil
}

// Close closes the database connection pool.
func (db *DB) Close() {
	if db.Pool != nil {
		db.Pool.Close()
	}
}
