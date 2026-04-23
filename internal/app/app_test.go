package app

import (
	"testing"

	"research/pipeline"
)

func TestParseArgsDefaults(t *testing.T) {
	args, err := ParseArgs([]string{})
	if err != nil {
		t.Fatalf("ParseArgs returned error: %v", err)
	}
	if args.Cap != nil {
		t.Fatalf("expected nil cap")
	}
	if args.Phase != "all" || args.OutputDir != "./data" || args.Format != "csv" {
		t.Fatalf("unexpected defaults: %+v", args)
	}
}

func TestParseArgsAllFlags(t *testing.T) {
	args, err := ParseArgs([]string{"--cap", "10", "--phase", "2,3", "--output-dir", "/tmp/out", "--skip-scoring", "--company-info", "--format", "csv"})
	if err != nil {
		t.Fatalf("ParseArgs returned error: %v", err)
	}
	if args.Cap == nil || *args.Cap != 10 {
		t.Fatalf("expected cap=10, got %+v", args.Cap)
	}
	if !args.SkipScoring || !args.CompanyInfo {
		t.Fatalf("expected true flags")
	}
}

func TestFilterTrialsByPhase(t *testing.T) {
	trials := []pipeline.Trial{
		{NCTID: "NCT001", Phase: "PHASE1"},
		{NCTID: "NCT002", Phase: "PHASE2"},
		{NCTID: "NCT003", Phase: "PHASE3"},
		{NCTID: "NCT004", Phase: "PHASE1, PHASE2"},
	}
	filtered := FilterTrialsByPhase(trials, "2")
	if len(filtered) != 2 {
		t.Fatalf("expected 2 trials, got %d", len(filtered))
	}
}
