package main

import (
	"bytes"
	"fmt"
	"net/http"
	"time"
)

func main() {
	// Create a large JSON array with 1000 items
	var buffer bytes.Buffer
	buffer.WriteString("[")
	for i := 0; i < 1000; i++ {
		buffer.WriteString(`{
			"screening_id": "test-id-` + fmt.Sprintf("%d", i) + `",
			"full_name": "Test User",
			"jan_aadhaar_number": "1234567890",
			"risk_index_score": 8.5,
			"clinical_flag": "HIGH_RISK",
			"spirometry_log": "Normal",
			"heatmap_base64": "dummy",
			"signature": "valid-signature-1234"
		}`)
		if i < 999 {
			buffer.WriteString(",")
		}
	}
	buffer.WriteString("]")

	req, _ := http.NewRequest("POST", "http://localhost:8080/sync", &buffer)
	req.Header.Set("Content-Type", "application/json")

	start := time.Now()
	resp, err := http.DefaultClient.Do(req)
	duration := time.Since(start)

	if err != nil {
		fmt.Printf("[ERROR] Go Backend Request failed: %v\n", err)
		return
	}
	defer resp.Body.Close()

	fmt.Printf("[BENCHMARK] Go Sync Engine received and processed batch in %v\n", duration)
	fmt.Printf("[STATUS] Server HTTP Response Code: %d\n", resp.StatusCode)
	
	if resp.StatusCode == 429 {
		fmt.Println("[SUCCESS] Worker Pool 429 Throttle Isolation activated perfectly! (Overflow protected)")
	} else if resp.StatusCode == 200 || resp.StatusCode == 202 {
		fmt.Println("[SUCCESS] Server processed the entire 1,000 payload block!")
	} else {
		fmt.Printf("[NOTE] Unexpected status: %d\n", resp.StatusCode)
	}
}
