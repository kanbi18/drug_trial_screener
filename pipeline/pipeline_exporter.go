package pipeline

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

var TrialColumns = []string{
	"ticker",
	"company",
	"nct_id",
	"title",
	"phase",
	"status",
	"therapeutic_area",
	"enrollment_count",
	"is_multi_site",
	"start_date",
	"base_rate",
	"readiness_score",
	"readiness_rationale",
	"analyst_estimate",
}

var CompanyColumns = []string{
	"ticker",
	"company_name",
	"market_cap",
	"sector",
	"industry",
	"exchange",
	"fda_approved_drugs_count",
	"active_trial_count",
	"avg_readiness_score",
}

func ExportTrialsCSV(trials []Trial, outputDir, filename, maxCapLabel string) (string, error) {
	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return "", err
	}
	if filename == "" {
		today := time.Now().Format("2006-01-02")
		if maxCapLabel != "" {
			filename = fmt.Sprintf("trials_cap_%s_%s.csv", maxCapLabel, today)
		} else {
			filename = fmt.Sprintf("trials_all_%s.csv", today)
		}
	}

	path := filepath.Join(outputDir, filename)
	f, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write(TrialColumns); err != nil {
		return "", err
	}
	for _, t := range trials {
		record := []string{
			t.Ticker,
			t.Company,
			t.NCTID,
			t.Title,
			t.Phase,
			t.Status,
			stringPtr(t.TherapeuticArea),
			intPtrToString(t.EnrollmentCount),
			boolPtrToString(t.IsMultiSite),
			t.StartDate,
			floatPtrToString(t.BaseRate),
			intPtrToString(t.ReadinessScore),
			stringPtr(t.ReadinessRationale),
			floatPtrToString(t.AnalystEstimate),
		}
		if err := w.Write(record); err != nil {
			return "", err
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return "", err
	}

	fmt.Printf("Trials CSV written: %s (%d rows)\n", path, len(trials))
	return path, nil
}

func ExportCompaniesCSV(companies []CompanyInfo, outputDir, filename string) (string, error) {
	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return "", err
	}
	if filename == "" {
		filename = fmt.Sprintf("company_info_%s.csv", time.Now().Format("2006-01-02"))
	}

	path := filepath.Join(outputDir, filename)
	f, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write(CompanyColumns); err != nil {
		return "", err
	}
	for _, c := range companies {
		record := []string{
			c.Ticker,
			c.CompanyName,
			floatPtrToString(c.MarketCap),
			c.Sector,
			c.Industry,
			c.Exchange,
			strconv.Itoa(c.FDAApprovedDrugsCount),
			strconv.Itoa(c.ActiveTrialCount),
			floatPtrToString(c.AvgReadinessScore),
		}
		if err := w.Write(record); err != nil {
			return "", err
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return "", err
	}

	fmt.Printf("Company CSV written: %s (%d rows)\n", path, len(companies))
	return path, nil
}

func ExportCompanyListCSV(companies []Company, outputDir, filename string) (string, error) {
	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return "", err
	}
	if filename == "" {
		filename = "companies_universe.csv"
	}

	path := filepath.Join(outputDir, filename)
	f, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	headers := []string{"symbol", "name", "marketCap", "sector", "industry", "exchange"}
	if err := w.Write(headers); err != nil {
		return "", err
	}
	for _, c := range companies {
		record := []string{
			c.Symbol,
			c.Name,
			strconv.FormatFloat(c.MarketCap, 'f', -1, 64),
			c.Sector,
			c.Industry,
			c.Exchange,
		}
		if err := w.Write(record); err != nil {
			return "", err
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return "", err
	}

	fmt.Printf("Company list written: %s (%d rows)\n", path, len(companies))
	return path, nil
}

func stringPtr(v *string) string {
	if v == nil {
		return ""
	}
	return *v
}

func intPtrToString(v *int) string {
	if v == nil {
		return ""
	}
	return strconv.Itoa(*v)
}

func boolPtrToString(v *bool) string {
	if v == nil {
		return ""
	}
	if *v {
		return "true"
	}
	return "false"
}

func floatPtrToString(v *float64) string {
	if v == nil {
		return ""
	}
	return strings.TrimRight(strings.TrimRight(strconv.FormatFloat(*v, 'f', 6, 64), "0"), ".")
}
