"""
Unit tests for MLOps tool pattern matching utilities.
"""

from claude_builder.utils.file_patterns import FilePatterns


class TestMLOpsPatterns:
    """Test suite for MLOps tool pattern detection."""

    def test_dvc_detection(self, temp_dir):
        """Test DVC project detection."""
        (temp_dir / ".dvc").mkdir()
        (temp_dir / "dvc.yaml").touch()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "dvc" in detected
        assert detected["dvc"] > 8.0

    def test_mlflow_detection(self, temp_dir):
        """Test MLflow project detection."""
        (temp_dir / "mlflow").mkdir()
        (temp_dir / "mlruns").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "mlflow" in detected
        assert detected["mlflow"] > 8.0

    def test_airflow_prefect_dagster_detection(self, temp_dir):
        """Test Airflow, Prefect, and Dagster detection."""
        (temp_dir / "airflow" / "dags").mkdir(parents=True)
        (temp_dir / "prefect").mkdir()
        (temp_dir / "dagster").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "airflow" in detected
        assert "prefect" in detected
        assert "dagster" in detected
        assert detected["airflow"] > 4.0
        assert detected["prefect"] > 4.0
        assert detected["dagster"] > 4.0

    def test_dbt_detection(self, temp_dir):
        """Test dbt project detection."""
        (temp_dir / "dbt_project.yml").touch()
        (temp_dir / "models").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "dbt" in detected
        assert detected["dbt"] > 4.0

    def test_great_expectations_detection(self, temp_dir):
        """Test Great Expectations project detection."""
        (temp_dir / "great_expectations").mkdir()
        (temp_dir / "checkpoints").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "great_expectations" in detected
        assert detected["great_expectations"] > 4.0

    def test_serving_detection(self, temp_dir):
        """Test model serving tool detection."""
        (temp_dir / "bentoml").mkdir()
        (temp_dir / "kubeflow").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "bentoml" in detected
        assert "kubeflow" in detected
        assert detected["bentoml"] > 4.0
        assert detected["kubeflow"] > 4.0

    def test_feast_detection(self, temp_dir):
        """Test Feast feature store detection."""
        (temp_dir / "feature_store.yaml").touch()
        (temp_dir / "feast").mkdir()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "feast" in detected
        assert detected["feast"] > 4.0

    def test_notebooks_kedro_detection(self, temp_dir):
        """Test notebooks and Kedro detection."""
        (temp_dir / "notebooks").mkdir()
        (temp_dir / "notebooks" / "analysis.ipynb").touch()
        (temp_dir / "kedro.yml").touch()

        detected = FilePatterns.detect_mlops_tools(temp_dir)

        assert "notebooks" in detected
        assert "kedro" in detected
        assert detected["notebooks"] > 4.0
        assert detected["kedro"] > 2.0


class TestMLOpsIntegration:
    """Test suite for integrated MLOps pattern detection."""

    def test_all_tools_aggregator_includes_mlops(self, temp_dir):
        """Test that the main aggregator includes MLOps tools."""
        # Create some MLOps tool indicators
        (temp_dir / ".dvc").mkdir()
        (temp_dir / "mlruns").mkdir()

        # Create other DevOps tool indicators
        (temp_dir / "main.tf").touch()  # Infrastructure
        (temp_dir / "prometheus.yml").touch()  # Observability
        (temp_dir / ".trivyignore").touch()  # Security

        all_detected = FilePatterns.detect_all_devops_tools(temp_dir)

        assert "mlops" in all_detected
        assert "dvc" in all_detected["mlops"]
        assert "mlflow" in all_detected["mlops"]

        # Ensure other categories are still present
        assert "infrastructure" in all_detected
        assert "observability" in all_detected
        assert "security" in all_detected
