package pipeline

import "testing"

func TestModelStubs(t *testing.T) {
	if err := TrainModel("fake.csv", ""); err == nil {
		t.Fatalf("expected TrainModel to return not implemented error")
	}
	if _, err := PredictSuccessProbability(map[string]any{"phase": "PHASE2"}); err == nil {
		t.Fatalf("expected PredictSuccessProbability to return not implemented error")
	}
	if _, err := PrepareFeaturesFromTrial(Trial{}, nil); err == nil {
		t.Fatalf("expected PrepareFeaturesFromTrial to return not implemented error")
	}
	if ModelDir == "" || ModelPath == "" {
		t.Fatalf("expected model constants")
	}
}
