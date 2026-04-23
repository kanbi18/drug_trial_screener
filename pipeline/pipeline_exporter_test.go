package pipeline

import (
	"encoding/csv"
	"os"
	"path/filepath"
	"testing"
)

func TestExportTrialsCSV(t *testing.T) {
	dir := t.TempDir()
	path, err := ExportTrialsCSV([]Trial{{Ticker: "ABC", NCTID: "NCT001"}}, dir, "test.csv", "")
	if err != nil {
		t.Fatalf("ExportTrialsCSV returned error: %v", err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected file to exist: %v", err)
	}

	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open csv: %v", err)
	}
	defer f.Close()
	recs, err := csv.NewReader(f).ReadAll()
	if err != nil {
		t.Fatalf("read csv: %v", err)
	}
	if len(recs[0]) != len(TrialColumns) {
		t.Fatalf("unexpected columns: %d", len(recs[0]))
	}
}

func TestExportCompanyListCSV(t *testing.T) {
	dir := t.TempDir()
	path, err := ExportCompanyListCSV([]Company{{Symbol: "X", Name: "X", MarketCap: 1e9}}, dir, "custom.csv")
	if err != nil {
		t.Fatalf("ExportCompanyListCSV returned error: %v", err)
	}
	if filepath.Base(path) != "custom.csv" {
		t.Fatalf("expected custom.csv, got %s", filepath.Base(path))
	}
}
