"""MLOps and data pipeline detection for project analysis.

This module provides detection of MLOps tools and data pipeline frameworks
commonly used in machine learning and data engineering projects.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from claude_builder.analysis.detectors.base import BaseDetector


class MLOpsDetector(BaseDetector):
    """Detector for MLOps tools and data pipeline frameworks."""

    def __init__(self) -> None:
        super().__init__()
        # Internal patterns for MLOps detection
        self._patterns = {
            # Data Version Control
            "dvc": {
                "files": ["dvc.yaml", "dvc.lock", ".dvcignore"],
                "dirs": [".dvc"],
                "globs": ["*.dvc"],
            },
            # MLflow for ML lifecycle management
            "mlflow": {
                "files": ["MLproject", "mlflow.yml"],
                "dirs": ["mlruns", "mlartifacts"],
                "globs": [],
            },
            # Apache Airflow for workflow orchestration
            "airflow": {
                "files": ["airflow.cfg"],
                "dirs": ["airflow/dags", "dags"],
                "globs": [],
            },
            # Prefect for workflow orchestration
            "prefect": {
                "files": ["prefect.yaml", "deployment.yaml"],
                "dirs": ["prefect", ".prefect"],
                "globs": [],
            },
            # Dagster for data orchestration
            "dagster": {
                "files": ["workspace.yaml", "dagster.yaml"],
                "dirs": ["dagster"],
                "globs": [],
            },
            # dbt for data transformation
            "dbt": {
                "files": ["dbt_project.yml", "profiles.yml"],
                "dirs": ["dbt", "models", "macros", "seeds"],
                "globs": [],
            },
            # Great Expectations for data quality
            "great_expectations": {
                "files": ["great_expectations.yml"],
                "dirs": ["great_expectations", "expectations", "gx"],
                "globs": [],
            },
            # Feast for feature store
            "feast": {
                "files": ["feature_store.yaml", "feast.py"],
                "dirs": ["feast", "feature_repo"],
                "globs": [],
            },
            # BentoML for model serving
            "bentoml": {
                "files": ["bentofile.yaml", "bentoml.yml"],
                "dirs": ["bentoml", "bentos"],
                "globs": [],
            },
            # Kubeflow for ML on Kubernetes
            "kubeflow": {
                "files": ["kubeflow.yaml", "kustomization.yaml"],
                "dirs": ["kubeflow", ".kubeflow"],
                "globs": [],
            },
            # Notebooks (ambiguous, low confidence only)
            "notebooks": {
                "files": [],
                "dirs": ["notebooks", "notebook", "jupyter"],
                "globs": ["*.ipynb"],
            },
        }

    def _calculate_confidence(self, project_path: Path, tool: str) -> int:
        """Calculate confidence score for a specific MLOps tool."""
        confidence = 0
        patterns = self._patterns.get(tool, {})

        # Files (+3)
        for file_pattern in patterns.get("files", []):
            if (project_path / file_pattern).exists():
                confidence += 3

        # Dirs (+5)
        for dir_pattern in patterns.get("dirs", []):
            if (project_path / dir_pattern).is_dir():
                confidence += 5

        # Globs (+4)
        for glob_pattern in patterns.get("globs", []):
            if list(project_path.glob(glob_pattern)):
                confidence += 4

        return confidence

    def _has_strong_ml_signals(self, project_path: Path) -> bool:
        """Heuristic to check strong ML signals to allow notebook inclusion."""
        ml_dirs = [
            "models/",
            "data/",
            "datasets/",
            "training/",
            "experiments/",
            "ml/",
            "src/models/",
            "src/data/",
        ]

        for indicator in ml_dirs:
            if (project_path / indicator).exists():
                if indicator.endswith("/"):
                    return True

        req_file = project_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text().lower()
                ml_packages = [
                    "scikit-learn",
                    "tensorflow",
                    "pytorch",
                    "pandas",
                    "numpy",
                    "matplotlib",
                ]
                if any(pkg in content for pkg in ml_packages):
                    return True
            except Exception:
                pass

        return False

    def detect(self, project_path: Optional[Path] = None) -> Dict[str, List[str]]:
        """Detect MLOps tools and categorize them."""
        results: Dict[str, List[str]] = {"data_pipeline": [], "mlops_tools": []}

        target = project_path or self.project_path
        if target is None:
            return results

        data_pipeline_tools = {
            "airflow",
            "prefect",
            "dagster",
            "dbt",
            "dvc",
            "great_expectations",
        }
        mlops_tools = {"mlflow", "feast", "kubeflow", "bentoml"}

        for tool in self._patterns.keys():
            if tool == "notebooks":
                continue
            confidence = self._calculate_confidence(target, tool)
            if confidence > 0:
                if tool in data_pipeline_tools:
                    results["data_pipeline"].append(tool)
                elif tool in mlops_tools:
                    results["mlops_tools"].append(tool)

        # Notebooks only if additional ML signals exist
        notebook_confidence = self._calculate_confidence(target, "notebooks")
        if notebook_confidence > 0 and self._has_strong_ml_signals(target):
            results["mlops_tools"].append("notebooks")

        return results

    def detect_with_confidence(
        self, project_path: Optional[Path] = None
    ) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """Detect MLOps tools with confidence levels."""
        results: Dict[str, List[str]] = {"data_pipeline": [], "mlops_tools": []}
        bucket_map: Dict[str, str] = {}

        target = project_path or self.project_path
        if target is None:
            return results, bucket_map

        data_pipeline_tools = {
            "airflow",
            "prefect",
            "dagster",
            "dbt",
            "dvc",
            "great_expectations",
        }
        mlops_tools = {"mlflow", "feast", "kubeflow", "bentoml"}

        for tool in self._patterns.keys():
            if tool == "notebooks":
                continue
            confidence = self._calculate_confidence(target, tool)
            if confidence > 0:
                if confidence >= 12:
                    bucket = "high"
                elif confidence >= 8:
                    bucket = "medium"
                else:
                    bucket = "low"
                bucket_map[tool] = bucket
                if tool in data_pipeline_tools:
                    results["data_pipeline"].append(tool)
                elif tool in mlops_tools:
                    results["mlops_tools"].append(tool)

        notebook_confidence = self._calculate_confidence(target, "notebooks")
        if notebook_confidence > 0 and self._has_strong_ml_signals(target):
            if notebook_confidence >= 12:
                bucket = "high"
            elif notebook_confidence >= 8:
                bucket = "medium"
            else:
                bucket = "low"
            bucket_map["notebooks"] = bucket
            results["mlops_tools"].append("notebooks")

        return results, bucket_map
