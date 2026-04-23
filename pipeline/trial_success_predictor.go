package pipeline

import (
	"errors"
	"path/filepath"
)

var ModelDir = filepath.Join("models")
var ModelPath = filepath.Join(ModelDir, "trial_predictor.pkl")

func TrainModel(trainingDataPath string, outputPath string) error {
	return errors.New("ML model training is not yet implemented")
}

func PredictSuccessProbability(trialFeatures map[string]any) (float64, error) {
	return 0, errors.New("ML prediction is not yet implemented")
}

func PrepareFeaturesFromTrial(trial Trial, companyData *CompanyData) (map[string]any, error) {
	return nil, errors.New("feature preparation is not yet implemented")
}
