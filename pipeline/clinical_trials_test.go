package pipeline

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCleanCompanyName(t *testing.T) {
	got := CleanCompanyName("Vertex Therapeutics, Inc.")
	if got != "Vertex" {
		t.Fatalf("unexpected clean name: %s", got)
	}
}

func TestFetchTrialsParsesFields(t *testing.T) {
	oldURL := ClinicalTrialsURL
	oldClient := HTTPClient
	defer func() {
		ClinicalTrialsURL = oldURL
		HTTPClient = oldClient
	}()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{
			"studies":[
				{
					"hasResults":false,
					"protocolSection":{
						"identificationModule":{"nctId":"NCT12345678","briefTitle":"Phase II Cancer Study"},
						"designModule":{"phases":["PHASE2"],"enrollmentInfo":{"count":150}},
						"statusModule":{"overallStatus":"RECRUITING","startDateStruct":{"date":"2025-03-01"}},
						"conditionsModule":{"conditions":["Breast Cancer"]},
						"contactsLocationsModule":{"locations":[{"facility":"A"},{"facility":"B"}]}
					}
				}
			]
		}`))
	}))
	defer server.Close()

	ClinicalTrialsURL = server.URL
	HTTPClient = server.Client()

	trials, err := FetchTrials("TestCo", nil, 50)
	if err != nil {
		t.Fatalf("FetchTrials returned error: %v", err)
	}
	if len(trials) != 1 {
		t.Fatalf("expected 1 trial, got %d", len(trials))
	}
	if trials[0].NCTID != "NCT12345678" || trials[0].LocationsCount != 2 {
		t.Fatalf("unexpected parsed trial: %+v", trials[0])
	}
}
