package pipeline

import (
	"net/http"
	"time"
)

var HTTPClient = &http.Client{Timeout: 15 * time.Second}

type Company struct {
	Symbol    string
	Name      string
	MarketCap float64
	Sector    string
	Industry  string
	Exchange  string
}

type Trial struct {
	Ticker             string
	Company            string
	NCTID              string
	Title              string
	Phase              string
	Status             string
	Conditions         []string
	EnrollmentCount    *int
	LocationsCount     int
	StartDate          string
	HasResults         bool
	TherapeuticArea    *string
	IsMultiSite        *bool
	BaseRate           *float64
	ReadinessScore     *int
	ReadinessRationale *string
	AnalystEstimate    *float64
}

type CompanyInfo struct {
	Ticker                string
	CompanyName           string
	MarketCap             *float64
	Sector                string
	Industry              string
	Exchange              string
	FDAApprovedDrugsCount int
	ActiveTrialCount      int
	AvgReadinessScore     *float64
}

type CompanyData struct {
	MarketCap        *float64
	FDAApprovalCount *int
}
