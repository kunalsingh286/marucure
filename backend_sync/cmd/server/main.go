package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"log"
	"net/http"
	"os"

	"rajcxr/sync_backend/internal/api"
	"rajcxr/sync_backend/internal/cloud"
	"rajcxr/sync_backend/internal/db"
	"rajcxr/sync_backend/internal/identity"
)

func main() {
	dbConnString := os.Getenv("DATABASE_URL")
	if dbConnString == "" {
		dbConnString = "postgres://postgres:postgres@localhost:5432/rajcxr?sslmode=disable"
	}

	database, err := db.Connect(context.Background(), dbConnString)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	s3Client := cloud.NewS3Client("rajcxr-heatmaps-bucket")

	// Plug-and-Play Sovereign Gateway Configuration
	var identitySvc identity.IIdentityService
	stateURL := os.Getenv("STATE_GATEWAY_URL")
	if stateURL == "https://apitest.sewadwaar.rajasthan.gov.in" {
		identitySvc = identity.NewProductionJanAadhaarService(stateURL)
		log.Println("Injecting Production Jan Aadhaar Service (mTLS Gateway)")
	} else {
		identitySvc = identity.NewMockIdentityService()
		log.Println("Injecting Mock Identity Service (Sandbox Mode)")
	}

	serverAPI := api.NewAPI(database, s3Client, identitySvc)

	// Phase 3: Enforcing Strict mTLS Configuration
	tlsConfig := &tls.Config{
		ClientAuth:               tls.RequireAndVerifyClientCert,
		MinVersion:               tls.VersionTLS13, // Mandate modern encryption
		PreferServerCipherSuites: true,
	}

	// We load the CA certificate to verify incoming client (tablet) certs
	caCert, err := os.ReadFile("certs/ca.crt")
	if err == nil {
		caCertPool := x509.NewCertPool()
		caCertPool.AppendCertsFromPEM(caCert)
		tlsConfig.ClientCAs = caCertPool
	} else {
		log.Println("[WARNING] No CA cert found, falling back to soft-verification for local testing.")
		tlsConfig.ClientAuth = tls.NoClientCert // Fallback for local sandbox if certs missing
	}

	server := &http.Server{
		Addr:      ":8081",
		Handler:   serverAPI.Routes(),
		TLSConfig: tlsConfig,
	}

	log.Println("Starting MaruCure Silicosis Triage Engine (mTLS Secure Node) on port 8081...")
	if err := server.ListenAndServeTLS("certs/server.crt", "certs/server.key"); err != nil {
		log.Fatalf("mTLS Server failed to start: %v", err)
	}
}
