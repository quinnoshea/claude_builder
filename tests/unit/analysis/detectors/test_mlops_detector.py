"""Comprehensive tests for MLOpsDetector."""

import tempfile

from pathlib import Path

import pytest

from claude_builder.analysis.detectors.mlops import MLOpsDetector


class TestMLOpsDetector:
    """Test suite for MLOpsDetector class."""

    @pytest.fixture
    def temp_project_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            yield project_path

    @pytest.fixture
    def detector(self):
        return MLOpsDetector()

    def test_detect_empty_project(self, detector, temp_project_dir):
        result = detector.detect(temp_project_dir)
        assert result["data_pipeline"] == []
        assert result["mlops_tools"] == []

    def test_dvc_detection_high_confidence(self, detector, temp_project_dir):
        (temp_project_dir / ".dvc").mkdir()
        (temp_project_dir / "dvc.yaml").write_text("stages:\n  train:")
        (temp_project_dir / "dvc.lock").write_text("schema: '2.0'")
        (temp_project_dir / "model.dvc").write_text("outs:\n- path: model.pkl")

        result = detector.detect(temp_project_dir)
        categorized, buckets = detector.detect_with_confidence(temp_project_dir)
        assert "dvc" in result["data_pipeline"]
        assert buckets["dvc"] == "high"

    def test_mlflow_detection_high_confidence(self, detector, temp_project_dir):
        (temp_project_dir / "mlruns").mkdir()
        (temp_project_dir / "mlartifacts").mkdir()
        (temp_project_dir / "MLproject").write_text("name: test")

        result = detector.detect(temp_project_dir)
        categorized, buckets = detector.detect_with_confidence(temp_project_dir)
        assert "mlflow" in result["mlops_tools"]
        assert buckets["mlflow"] == "high"

    def test_airflow_detection_medium(self, detector, temp_project_dir):
        (temp_project_dir / "dags").mkdir()
        (temp_project_dir / "airflow.cfg").write_text("[core]\ndags_folder = dags")
        categorized, buckets = detector.detect_with_confidence(temp_project_dir)
        assert "airflow" in categorized["data_pipeline"]
        assert buckets["airflow"] == "medium"

    def test_notebooks_only_with_ml_signals(self, detector, temp_project_dir):
        (temp_project_dir / "notebooks").mkdir()
        (temp_project_dir / "analysis.ipynb").write_text("{}")
        # no ML signals yet
        result = detector.detect(temp_project_dir)
        assert "notebooks" not in result["mlops_tools"]

        # add ML signals
        (temp_project_dir / "models").mkdir()
        result2 = detector.detect(temp_project_dir)
        assert "notebooks" in result2["mlops_tools"]
