package pipeline

import (
	"strings"
	"testing"
)

func TestGetBaseRate(t *testing.T) {
	if GetBaseRate("PHASE1") != 0.08 {
		t.Fatalf("expected PHASE1 base rate")
	}
	if GetBaseRate("PHASE1, PHASE2") != 0.15 {
		t.Fatalf("expected highest base rate from multiple phases")
	}
}

func TestDetectTherapeuticArea(t *testing.T) {
	area, mod := DetectTherapeuticArea("HIV Vaccine Study", []string{"HIV"})
	if area != "Infectious Disease" || mod != 0.02 {
		t.Fatalf("unexpected area detection: %s %.2f", area, mod)
	}
}

func TestCalculateReadinessScore(t *testing.T) {
	enroll := 200
	trial := Trial{
		Title:           "Alzheimer Treatment",
		Phase:           "PHASE2",
		Status:          "RECRUITING",
		Conditions:      []string{"Alzheimer"},
		EnrollmentCount: &enroll,
		LocationsCount:  5,
	}

	score, baseRate, area, rationale := CalculateReadinessScore(trial, nil)
	if score < 0 || score > 100 {
		t.Fatalf("score out of range: %d", score)
	}
	if baseRate != 0.15 {
		t.Fatalf("unexpected base rate: %f", baseRate)
	}
	if area != "CNS / Neurology" {
		t.Fatalf("unexpected area: %s", area)
	}
	if !strings.Contains(rationale, ";") {
		t.Fatalf("expected multi-factor rationale: %s", rationale)
	}
}
