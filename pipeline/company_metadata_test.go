package pipeline

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGetFDAApprovalCount(t *testing.T) {
	oldURL := OpenFDADrugURL
	oldClient := HTTPClient
	defer func() {
		OpenFDADrugURL = oldURL
		HTTPClient = oldClient
	}()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"meta":{"results":{"total":42}}}`))
	}))
	defer server.Close()

	OpenFDADrugURL = server.URL
	HTTPClient = server.Client()

	count, err := GetFDAApprovalCount("Pfizer")
	if err != nil {
		t.Fatalf("GetFDAApprovalCount returned error: %v", err)
	}
	if count != 42 {
		t.Fatalf("expected 42, got %d", count)
	}
}

func TestBuildCompanyTable(t *testing.T) {
	oldURL := OpenFDADrugURL
	oldClient := HTTPClient
	defer func() {
		OpenFDADrugURL = oldURL
		HTTPClient = oldClient
	}()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"meta":{"results":{"total":2}}}`))
	}))
	defer server.Close()

	OpenFDADrugURL = server.URL
	HTTPClient = server.Client()

	companies := []Company{{Symbol: "XYZ", Name: "XYZ Corp.", MarketCap: 1e9, Sector: "Healthcare", Industry: "Biotechnology", Exchange: "NYSE"}}
	s1 := 60
	s2 := 80
	trials := []Trial{{Ticker: "XYZ", ReadinessScore: &s1}, {Ticker: "XYZ", ReadinessScore: &s2}}

	rows, err := BuildCompanyTable(companies, trials)
	if err != nil {
		t.Fatalf("BuildCompanyTable returned error: %v", err)
	}
	if len(rows) != 1 || rows[0].ActiveTrialCount != 2 {
		t.Fatalf("unexpected table rows: %+v", rows)
	}
}
