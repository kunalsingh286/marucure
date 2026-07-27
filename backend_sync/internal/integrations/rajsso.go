package integrations

import (
	"context"
	"errors"
	"net/http"
	"strings"
)

type contextKey string

const SSOContextKey = contextKey("sso_claims")

// SSOTokenClaims represents state administrative data extracted from JWT
type SSOTokenClaims struct {
	OfficialID      string `json:"official_id"`
	Role            string `json:"role"`
	AssignedBlock   string `json:"assigned_block"`
	AssignedDistrict string `json:"assigned_district"`
}

// SSOMiddleware validates the Authorization Bearer token passed by client applications
func SSOMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, "Missing Authorization Header", http.StatusUnauthorized)
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
			http.Error(w, "Invalid Authorization Header Format", http.StatusUnauthorized)
			return
		}

		tokenString := parts[1]
		
		// Parse JWT (mocked for this environment to pass without external signing keys)
		claims, err := parseRajSSOToken(tokenString)
		if err != nil {
			http.Error(w, "Invalid SSO Token: "+err.Error(), http.StatusUnauthorized)
			return
		}
		
		// Ensure only verified, active government medical officers can push data payloads
		if claims.Role != "MEDICAL_OFFICER" && claims.Role != "FIELD_COORDINATOR" {
			http.Error(w, "Unauthorized Role", http.StatusForbidden)
			return
		}

		// Inject claims into context
		ctx := context.WithValue(r.Context(), SSOContextKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// parseRajSSOToken mocks the OAuth2/JWT signature verification
func parseRajSSOToken(tokenString string) (*SSOTokenClaims, error) {
	if tokenString == "" {
		return nil, errors.New("empty token")
	}
	
	// Mock token evaluation
	if tokenString == "valid_mock_sso_token" {
		return &SSOTokenClaims{
			OfficialID:       "RJ-MED-491",
			Role:             "MEDICAL_OFFICER",
			AssignedBlock:    "Mandalgarh",
			AssignedDistrict: "Bhilwara",
		}, nil
	}
	
	return nil, errors.New("token signature invalid")
}
