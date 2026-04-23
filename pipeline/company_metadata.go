package pipeline

import (
	"encoding/json"
	"fmt"
	"net/url"
)

var OpenFDADrugURL = "https://api.fda.gov/drug/drugsfda.json"

func GetFDAApprovalCount(companyName string) (int, error) {
	q := url.Values{}
	q.Set("search", fmt.Sprintf("openfda.manufacturer_name:\"%s\"", companyName))
	q.Set("limit", "1")

	resp, err := HTTPClient.Get(OpenFDADrugURL + "?" + q.Encode())
	if err != nil {
		return 0, nil
	}
	if resp.StatusCode >= 400 {
		_ = resp.Body.Close()
		return 0, nil
	}

	var payload struct {
		Meta struct {
			Results struct {
				Total int `json:"total"`
			} `json:"results"`
		} `json:"meta"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		_ = resp.Body.Close()
		return 0, nil
	}
	_ = resp.Body.Close()
	return payload.Meta.Results.Total, nil
}

func BuildCompanyTable(companies []Company, trialResults []Trial) ([]CompanyInfo, error) {
	rows := make([]CompanyInfo, 0, len(companies))
	for _, company := range companies {
		cleanName := CleanCompanyName(company.Name)
		fmt.Printf("  Fetching FDA data for %s...\n", cleanName)
		count, _ := GetFDAApprovalCount(cleanName)

		activeCount := 0
		total := 0.0
		scored := 0
		for _, t := range trialResults {
			if t.Ticker != company.Symbol {
				continue
			}
			activeCount++
			if t.ReadinessScore != nil {
				total += float64(*t.ReadinessScore)
				scored++
			}
		}

		var avg *float64
		if scored > 0 {
			v := mathRound1(total / float64(scored))
			avg = &v
		}
		marketCap := company.MarketCap

		rows = append(rows, CompanyInfo{
			Ticker:                company.Symbol,
			CompanyName:           cleanName,
			MarketCap:             &marketCap,
			Sector:                company.Sector,
			Industry:              company.Industry,
			Exchange:              company.Exchange,
			FDAApprovedDrugsCount: count,
			ActiveTrialCount:      activeCount,
			AvgReadinessScore:     avg,
		})
	}
	return rows, nil
}

func mathRound1(v float64) float64 {
	return float64(int(v*10+0.5)) / 10
}
