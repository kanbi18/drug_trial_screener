"""Tests for pipeline.ml_model module (stub validation)."""

import pytest
from pipeline.ml_model import (
    train_model,
    predict_success_probability,
    prepare_features_from_trial,
    MODEL_PATH,
    MODEL_DIR,
)


class TestModelStubs:
    def test_train_model_raises(self):
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            train_model("fake_path.csv")

    def test_predict_raises(self):
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            predict_success_probability({"phase": "PHASE2"})

    def test_prepare_features_raises(self):
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            prepare_features_from_trial({"phase": "PHASE2"})

    def test_model_path_is_pathlib(self):
        from pathlib import Path
        assert isinstance(MODEL_PATH, Path)

    def test_model_dir_ends_with_models(self):
        assert MODEL_DIR.name == "models"
