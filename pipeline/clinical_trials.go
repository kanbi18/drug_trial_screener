package pipeline

import (
	"encoding/json"
	"fmt"
	"net/url"
	"strings"
	"time"
)

var ClinicalTrialsURL = "https://clinicaltrials.gov/api/v2/studies"

const RequestDelay = 500 * time.Millisecond

func CleanCompanyName(name string) string {
	suffixes := []string{
		", Inc.", " Inc.", " Corp.", " PLC", " Ltd.", " Incorporated",
		" International", " Holdings", " Therapeutics", " Biosciences",
	}
	out := name
	for _, suffix := range suffixes {
		out = strings.ReplaceAll(out, suffix, "")
	}
	return strings.TrimSpace(out)
}

type ctResponse struct {
	Studies []ctStudy `json:"studies"`
}

type ctStudy struct {
	HasResults      bool `json:"hasResults"`
	ProtocolSection struct {
		IdentificationModule struct {
			NCTID      string `json:"nctId"`
			BriefTitle string `json:"briefTitle"`
		} `json:"identificationModule"`
		DesignModule struct {
			Phases         []string `json:"phases"`
			EnrollmentInfo struct {
				Count *int `json:"count"`
			} `json:"enrollmentInfo"`
		} `json:"designModule"`
		StatusModule struct {
			OverallStatus   string `json:"overallStatus"`
			StartDateStruct struct {
				Date string `json:"date"`
			} `json:"startDateStruct"`
		} `json:"statusModule"`
		ConditionsModule struct {
			Conditions []string `json:"conditions"`
		} `json:"conditionsModule"`
		ContactsLocationsModule struct {
			Locations []map[string]any `json:"locations"`
		} `json:"contactsLocationsModule"`
	} `json:"protocolSection"`
}

func FetchTrials(companyName string, statuses []string, pageSize int) ([]Trial, error) {
	if statuses == nil {
		statuses = []string{"RECRUITING", "NOT_YET_RECRUITING"}
	}
	if pageSize <= 0 {
		pageSize = 50
	}

	q := url.Values{}
	q.Set("query.spons", companyName)
	q.Set("filter.overallStatus", strings.Join(statuses, "|"))
	q.Set("pageSize", fmt.Sprintf("%d", pageSize))
	q.Set("format", "json")

	resp, err := HTTPClient.Get(ClinicalTrialsURL + "?" + q.Encode())
	if err != nil {
		fmt.Printf("  Error fetching trials for %s: %v\n", companyName, err)
		return []Trial{}, nil
	}
	if resp.StatusCode >= 400 {
		_ = resp.Body.Close()
		fmt.Printf("  Error fetching trials for %s: status %d\n", companyName, resp.StatusCode)
		return []Trial{}, nil
	}

	var payload ctResponse
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		_ = resp.Body.Close()
		fmt.Printf("  Error fetching trials for %s: %v\n", companyName, err)
		return []Trial{}, nil
	}
	_ = resp.Body.Close()

	parsed := make([]Trial, 0, len(payload.Studies))
	for _, study := range payload.Studies {
		locations := study.ProtocolSection.ContactsLocationsModule.Locations
		trial := Trial{
			NCTID:           study.ProtocolSection.IdentificationModule.NCTID,
			Title:           study.ProtocolSection.IdentificationModule.BriefTitle,
			Phase:           strings.Join(study.ProtocolSection.DesignModule.Phases, ", "),
			Status:          study.ProtocolSection.StatusModule.OverallStatus,
			Conditions:      study.ProtocolSection.ConditionsModule.Conditions,
			EnrollmentCount: study.ProtocolSection.DesignModule.EnrollmentInfo.Count,
			LocationsCount:  len(locations),
			StartDate:       study.ProtocolSection.StatusModule.StartDateStruct.Date,
			HasResults:      study.HasResults,
		}
		parsed = append(parsed, trial)
	}

	return parsed, nil
}

func FetchAllTrials(companies []Company, statuses []string) ([]Trial, error) {
	all := []Trial{}
	for _, company := range companies {
		cleanName := CleanCompanyName(company.Name)
		fmt.Printf("Searching trials for: %s...\n", cleanName)

		trials, err := FetchTrials(cleanName, statuses, 50)
		if err != nil {
			return nil, err
		}
		for _, trial := range trials {
			trial.Ticker = company.Symbol
			trial.Company = cleanName
			all = append(all, trial)
		}

		time.Sleep(RequestDelay)
	}
	return all, nil
}
