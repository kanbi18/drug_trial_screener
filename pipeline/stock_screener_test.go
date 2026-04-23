package pipeline

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGetPublicBiotechListRequiresKey(t *testing.T) {
	oldKey := FMPAPIKey
	defer func() { FMPAPIKey = oldKey }()
	FMPAPIKey = ""

	_, err := GetPublicBiotechList(nil, "NYSE")
	if err == nil {
		t.Fatalf("expected error when FMP_API_KEY is empty")
	}
}

func TestGetPublicBiotechListDedupes(t *testing.T) {
	oldURL := FMPScreenerURL
	oldKey := FMPAPIKey
	oldClient := HTTPClient
	defer func() {
		FMPScreenerURL = oldURL
		FMPAPIKey = oldKey
		HTTPClient = oldClient
	}()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"symbol":"DUP","companyName":"Dup Inc.","marketCap":1000000000,"sector":"Healthcare","industry":"Biotechnology","exchange":"NYSE"}]`))
	}))
	defer server.Close()

	FMPScreenerURL = server.URL
	FMPAPIKey = "test_key"
	HTTPClient = server.Client()

	companies, err := GetPublicBiotechList(nil, "NYSE")
	if err != nil {
		t.Fatalf("GetPublicBiotechList returned error: %v", err)
	}
	if len(companies) != 1 {
		t.Fatalf("expected 1 deduped company, got %d", len(companies))
	}
}
